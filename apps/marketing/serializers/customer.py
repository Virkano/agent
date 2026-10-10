# coding=utf-8
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.models import ApplicationAccessToken
from application.models.application_chat import Chat
from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCustomer,
    MarketingCustomerImportBatch,
    MarketingCustomerStatus,
    MarketingTask,
    MarketingTouchBatch,
    MarketingTouchExecution,
)
from marketing.importing import (
    IMPORT_FIELDS,
    normalize_identifier,
    parse_customer_import_file,
    resolve_mapping,
    validate_import_rows,
)


class MarketingCustomerWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, label=_("Customer name"))
    phone = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Phone or customer ID"))
    province = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Province"))
    current_plan = serializers.CharField(required=False, allow_blank=True, max_length=128, label=_("Current plan"))
    monthly_data_usage = serializers.CharField(
        required=False, allow_blank=True, max_length=64, label=_("Monthly data usage")
    )
    monthly_call_usage = serializers.CharField(
        required=False, allow_blank=True, max_length=64, label=_("Monthly call usage")
    )
    status = serializers.ChoiceField(required=False, choices=MarketingCustomerStatus.choices, label=_("Status"))
    intent = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Intent"))
    remark = serializers.CharField(required=False, allow_blank=True, label=_("Remark"))
    config = serializers.DictField(required=False, label=_("Config"))

    def validate_status(self, value):
        if value == MarketingCustomerStatus.CONVERTED:
            raise serializers.ValidationError("Use conversion record endpoint to confirm a customer conversion")
        return value


class MarketingCustomerListQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class MarketingCustomerBulkSerializer(serializers.Serializer):
    customers = serializers.ListField(child=MarketingCustomerWriteSerializer(), required=True)


class MarketingCustomerImportConfirmSerializer(serializers.Serializer):
    file_name = serializers.CharField(required=True, allow_blank=False, max_length=256)
    mapping = serializers.DictField(required=True)
    rows = serializers.ListField(child=serializers.DictField(), required=True, min_length=1, max_length=1000)


class MarketingCustomerFollowUpSerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=True, choices=MarketingCustomerStatus.choices, label=_("Status"))
    intent = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Intent"))
    note = serializers.CharField(required=True, allow_blank=False, max_length=2000, label=_("Follow-up note"))

    def validate_status(self, value):
        if value == MarketingCustomerStatus.CONVERTED:
            raise serializers.ValidationError("Use conversion record endpoint to confirm a customer conversion")
        return value


class MarketingConversionRecordWriteSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(
        choices=MarketingConversionOutcome.choices, required=True, label=_("Conversion outcome")
    )
    product_name = serializers.CharField(required=False, allow_blank=True, max_length=128, label=_("Product or plan"))
    note = serializers.CharField(required=True, allow_blank=False, max_length=2000, label=_("Conversion note"))
    batch_id = serializers.UUIDField(required=False, allow_null=True, label=_("Source touch batch"))

    def validate(self, attrs):
        if attrs["outcome"] == MarketingConversionOutcome.CONVERTED and not attrs.get("product_name", "").strip():
            raise serializers.ValidationError({"product_name": "Converted customer requires product or plan"})
        return attrs


def _mask_phone(phone: str):
    if not phone:
        return ""
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone


def _customer_chat_count(customer: MarketingCustomer):
    return Chat.objects.filter(
        application_id=customer.task.application_id,
        source__marketing_task_id=str(customer.task_id),
        source__marketing_customer_id=str(customer.id),
    ).count()


def _customer_chat_url(customer: MarketingCustomer):
    if not customer.task.application_id:
        return ""
    access_token = ApplicationAccessToken.objects.filter(
        application_id=customer.task.application_id,
        is_active=True,
    ).first()
    if access_token is None:
        return ""
    return (
        f"/admin/chat/{access_token.access_token}"
        f"?marketing_task_id={customer.task_id}&marketing_customer_id={customer.id}"
    )


def serialize_conversion_record(row: MarketingConversionRecord):
    return {
        "id": str(row.id),
        "task_id": str(row.task_id),
        "customer_id": str(row.customer_id),
        "customer_name": row.customer.name,
        "batch_id": str(row.batch_id) if row.batch_id else None,
        "batch_name": row.batch.name if row.batch else "",
        "outcome": row.outcome,
        "product_name": row.product_name,
        "note": row.note,
        "operator_name": row.user.nick_name or row.user.username if row.user else "",
        "create_time": row.create_time,
    }


def serialize_customer(row: MarketingCustomer):
    latest_conversion = (
        MarketingConversionRecord.objects.filter(workspace_id=row.workspace_id, task_id=row.task_id, customer_id=row.id)
        .select_related("batch", "user")
        .first()
    )
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "task_id": str(row.task_id),
        "name": row.name,
        "phone": row.phone,
        "phone_masked": _mask_phone(row.phone),
        "province": row.province,
        "current_plan": row.current_plan,
        "monthly_data_usage": row.monthly_data_usage,
        "monthly_call_usage": row.monthly_call_usage,
        "status": row.status,
        "intent": row.intent,
        "remark": row.remark,
        "chat_count": _customer_chat_count(row),
        "chat_url": _customer_chat_url(row),
        "latest_conversion": serialize_conversion_record(latest_conversion) if latest_conversion else None,
        "config": row.config or {},
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_customer_import_batch(row: MarketingCustomerImportBatch):
    return {
        "id": str(row.id),
        "task_id": str(row.task_id),
        "file_name": row.file_name,
        "total_count": row.total_count,
        "valid_count": row.valid_count,
        "imported_count": row.imported_count,
        "skipped_count": row.skipped_count,
        "error_count": row.error_count,
        "mapping": row.mapping or {},
        "error_rows": row.error_rows or [],
        "operator_name": row.user.nick_name or row.user.username if row.user else "",
        "create_time": row.create_time,
    }


class MarketingCustomerService:
    def __init__(self, workspace_id: str, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _get_task(self, task_id: str):
        task = MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).first()
        if task is None:
            raise AppApiException(404, _("Marketing task does not exist"))
        return task

    def _queryset(self, task_id: str):
        return (
            MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id=task_id)
            .select_related("task")
            .order_by("-update_time")
        )

    def list(self, task_id: str, params: dict):
        self._get_task(task_id)
        serializer = MarketingCustomerListQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        query_set = self._queryset(task_id)
        name = serializer.validated_data.get("name")
        status = serializer.validated_data.get("status")
        if name:
            query_set = query_set.filter(
                Q(name__icontains=name)
                | Q(phone__icontains=name)
                | Q(province__icontains=name)
                | Q(current_plan__icontains=name)
                | Q(remark__icontains=name)
            )
        if status:
            query_set = query_set.filter(status=status)
        return [serialize_customer(row) for row in query_set]

    def page(self, task_id: str, current_page: int, page_size: int, params: dict):
        records = self.list(task_id, params)
        start = (current_page - 1) * page_size
        return Page(len(records), records[start : start + page_size], current_page, page_size)

    def create(self, task_id: str, data: dict):
        task = self._get_task(task_id)
        serializer = MarketingCustomerWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        try:
            customer = MarketingCustomer.objects.create(
                workspace_id=self.workspace_id,
                task=task,
                name=values.get("name", ""),
                phone=values.get("phone", ""),
                province=values.get("province", ""),
                current_plan=values.get("current_plan", ""),
                monthly_data_usage=values.get("monthly_data_usage", ""),
                monthly_call_usage=values.get("monthly_call_usage", ""),
                status=values.get("status", MarketingCustomerStatus.PENDING),
                intent=values.get("intent", ""),
                remark=values.get("remark", ""),
                config=values.get("config", {}),
            )
        except IntegrityError:
            raise AppApiException(400, _("Marketing customer already exists"))
        return serialize_customer(customer)

    def bulk_create(self, task_id: str, data: dict):
        task = self._get_task(task_id)
        serializer = MarketingCustomerBulkSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        created = 0
        skipped = 0
        for values in serializer.validated_data.get("customers", []):
            try:
                MarketingCustomer.objects.create(
                    workspace_id=self.workspace_id,
                    task=task,
                    name=values.get("name", ""),
                    phone=values.get("phone", ""),
                    province=values.get("province", ""),
                    current_plan=values.get("current_plan", ""),
                    monthly_data_usage=values.get("monthly_data_usage", ""),
                    monthly_call_usage=values.get("monthly_call_usage", ""),
                    status=values.get("status", MarketingCustomerStatus.PENDING),
                    intent=values.get("intent", ""),
                    remark=values.get("remark", ""),
                    config=values.get("config", {}),
                )
                created += 1
            except IntegrityError:
                skipped += 1
        return {"created": created, "skipped": skipped}

    def preview_import(self, task_id: str, uploaded_file, raw_mapping=None):
        task = self._get_task(task_id)
        headers, source_rows = parse_customer_import_file(uploaded_file)
        mapping = resolve_mapping(headers, raw_mapping)
        existing_identifiers = {
            normalize_identifier(row.phone)
            for row in MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id=task.id).exclude(
                phone=""
            )
        }
        rows = validate_import_rows(headers, source_rows, mapping, existing_identifiers)
        return {
            "file_name": uploaded_file.name,
            "headers": headers,
            "mapping": mapping,
            "rows": rows,
            "summary": self._import_summary(rows),
        }

    def confirm_import(self, task_id: str, data: dict):
        task = self._get_task(task_id)
        serializer = MarketingCustomerImportConfirmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        source_rows = []
        for index, raw_row in enumerate(values["rows"], start=2):
            row_data = raw_row.get("data", raw_row)
            if not isinstance(row_data, dict):
                continue
            source_rows.append((raw_row.get("row_number", index), [row_data.get(field, "") for field in IMPORT_FIELDS]))
        headers = list(IMPORT_FIELDS)
        mapping = {field: field for field in IMPORT_FIELDS}
        existing_identifiers = {
            normalize_identifier(row.phone)
            for row in MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id=task.id).exclude(
                phone=""
            )
        }
        rows = validate_import_rows(headers, source_rows, mapping, existing_identifiers)
        ready_rows = [row for row in rows if row["status"] == "READY"]
        skipped_rows = [row for row in rows if row["status"] == "SKIPPED"]
        error_rows = [row for row in rows if row["status"] == "ERROR"]
        with transaction.atomic():
            batch = MarketingCustomerImportBatch.objects.create(
                workspace_id=self.workspace_id,
                task=task,
                user=self.user,
                file_name=values["file_name"].strip(),
                total_count=len(rows),
                valid_count=len(ready_rows),
                imported_count=len(ready_rows),
                skipped_count=len(skipped_rows),
                error_count=len(error_rows),
                mapping=values["mapping"],
                error_rows=[row for row in rows if row["status"] != "READY"][:100],
            )
            MarketingCustomer.objects.bulk_create(
                [
                    MarketingCustomer(
                        workspace_id=self.workspace_id,
                        task=task,
                        name=row["data"]["name"],
                        phone=row["data"]["phone"],
                        province=row["data"]["province"],
                        current_plan=row["data"]["current_plan"],
                        monthly_data_usage=row["data"]["monthly_data_usage"],
                        monthly_call_usage=row["data"]["monthly_call_usage"],
                        intent=row["data"]["intent"],
                        remark=row["data"]["remark"],
                        config={
                            "marketing_import_batch_id": str(batch.id),
                            "marketing_import_file_name": batch.file_name,
                        },
                    )
                    for row in ready_rows
                ]
            )
        return {"batch": serialize_customer_import_batch(batch), "rows": rows}

    def import_history(self, task_id: str):
        self._get_task(task_id)
        return [
            serialize_customer_import_batch(row)
            for row in MarketingCustomerImportBatch.objects.filter(
                workspace_id=self.workspace_id,
                task_id=task_id,
            ).select_related("user")[:20]
        ]

    @staticmethod
    def _import_summary(rows):
        return {
            "total_count": len(rows),
            "ready_count": sum(row["status"] == "READY" for row in rows),
            "skipped_count": sum(row["status"] == "SKIPPED" for row in rows),
            "error_count": sum(row["status"] == "ERROR" for row in rows),
        }

    def update(self, task_id: str, customer_id: str, data: dict):
        self._get_task(task_id)
        customer = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task_id,
            workspace_id=self.workspace_id,
        ).first()
        if customer is None:
            raise AppApiException(404, _("Marketing customer does not exist"))
        serializer = MarketingCustomerWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        for field in [
            "name",
            "phone",
            "province",
            "current_plan",
            "monthly_data_usage",
            "monthly_call_usage",
            "status",
            "intent",
            "remark",
            "config",
        ]:
            if field in values:
                setattr(customer, field, values[field])
        try:
            customer.save()
        except IntegrityError:
            raise AppApiException(400, _("Marketing customer already exists"))
        return serialize_customer(customer)

    def follow_up(self, task_id: str, customer_id: str, data: dict):
        self._get_task(task_id)
        customer = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task_id,
            workspace_id=self.workspace_id,
        ).first()
        if customer is None:
            raise AppApiException(404, _("Marketing customer does not exist"))
        serializer = MarketingCustomerFollowUpSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        config = dict(customer.config or {})
        history = list(config.get("marketing_follow_up_history") or [])[-49:]
        history.append(
            {
                "status": values["status"],
                "intent": values.get("intent", ""),
                "note": values["note"],
                "operator": getattr(self.user, "nick_name", "") or getattr(self.user, "username", ""),
                "created_at": timezone.now().isoformat(),
            }
        )
        config["marketing_follow_up_history"] = history
        customer.status = values["status"]
        customer.intent = values.get("intent", "")
        customer.config = config
        customer.save(update_fields=["status", "intent", "config", "update_time"])
        return serialize_customer(customer)

    def record_conversion(self, task_id: str, customer_id: str, data: dict):
        task = self._get_task(task_id)
        customer = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task_id,
            workspace_id=self.workspace_id,
        ).first()
        if customer is None:
            raise AppApiException(404, _("Marketing customer does not exist"))
        serializer = MarketingConversionRecordWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        batch = self._resolve_conversion_batch(task, customer, values.get("batch_id"))
        record = MarketingConversionRecord.objects.create(
            workspace_id=self.workspace_id,
            task=task,
            customer=customer,
            batch=batch,
            user=self.user,
            outcome=values["outcome"],
            product_name=values.get("product_name", "").strip(),
            note=values["note"],
        )
        config = dict(customer.config or {})
        config["marketing_latest_conversion"] = {
            "record_id": str(record.id),
            "outcome": record.outcome,
            "product_name": record.product_name,
            "batch_id": str(record.batch_id) if record.batch_id else None,
            "batch_name": record.batch.name if record.batch else "",
            "created_at": record.create_time.isoformat(),
        }
        customer.config = config
        if record.outcome == MarketingConversionOutcome.CONVERTED:
            customer.status = MarketingCustomerStatus.CONVERTED
            customer.intent = f"已确认办理：{record.product_name}"
        else:
            customer.status = MarketingCustomerStatus.NO_INTENT
            customer.intent = "已确认未办理"
        customer.save(update_fields=["status", "intent", "config", "update_time"])
        return serialize_conversion_record(record)

    def _resolve_conversion_batch(self, task, customer, batch_id):
        if batch_id:
            batch = MarketingTouchBatch.objects.filter(
                id=batch_id,
                task_id=task.id,
                workspace_id=self.workspace_id,
            ).first()
            if batch is None:
                raise AppApiException(400, _("Source touch batch does not exist in this task"))
            selected_customer_ids = {str(row.get("customer_id")) for row in (batch.customer_snapshot or [])}
            if selected_customer_ids and str(customer.id) not in selected_customer_ids:
                raise AppApiException(400, _("Customer is not included in the source touch batch"))
            return batch
        latest_execution = (
            MarketingTouchExecution.objects.filter(
                workspace_id=self.workspace_id,
                customer_id=customer.id,
                batch__task_id=task.id,
            )
            .select_related("batch")
            .first()
        )
        return latest_execution.batch if latest_execution else None

    def delete(self, task_id: str, customer_id: str):
        deleted, _ = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task_id,
            workspace_id=self.workspace_id,
        ).delete()
        if deleted == 0:
            raise AppApiException(404, _("Marketing customer does not exist"))
        return True
