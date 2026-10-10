# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： base_generate_human_message_step.py.py
    @date：2024/1/10 17:50
    @desc:
"""
from typing import List, Dict

from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage

from application.chat_pipeline.I_base_chat_pipeline import ParagraphPipelineModel
from application.chat_pipeline.step.generate_human_message_step.i_generate_human_message_step import \
    IGenerateHumanMessageStep
from application.models import ChatRecord
from common.utils.common import flat_map


class BaseGenerateHumanMessageStep(IGenerateHumanMessageStep):

    def execute(self, problem_text: str,
                paragraph_list: List[ParagraphPipelineModel],
                history_chat_record: List[ChatRecord],
                dialogue_number: int,
                max_paragraph_char_number: int,
                prompt: str,
                padding_problem_text: str = None,
                marketing_context: str = None,
                no_references_setting=None,
                system=None,
                **kwargs) -> List[BaseMessage]:
        prompt = prompt if (paragraph_list is not None and len(paragraph_list) > 0) else no_references_setting.get(
            'value')
        exec_problem_text = padding_problem_text if padding_problem_text is not None else problem_text
        # 客户画像和营销约束属于系统上下文，不应和用户问题混在同一条消息中。
        # 小模型会把混在用户消息里的“内部说明”误当成待复述内容。
        system_prompt = system or ""
        if marketing_context:
            system_prompt = f"{system_prompt}\n\n{marketing_context}".strip()
        start_index = len(history_chat_record) - dialogue_number
        history_message = [[history_chat_record[index].get_human_message(), history_chat_record[index].get_ai_message()]
                           for index in
                           range(start_index if start_index > 0 else 0, len(history_chat_record))]
        if system_prompt:
            return [SystemMessage(system_prompt), *flat_map(history_message),
                    self.to_human_message(prompt, exec_problem_text, max_paragraph_char_number, paragraph_list,
                                          no_references_setting)]

        return [*flat_map(history_message),
                self.to_human_message(prompt, exec_problem_text, max_paragraph_char_number, paragraph_list,
                                      no_references_setting)]

    @staticmethod
    def to_human_message(prompt: str,
                         problem: str,
                         max_paragraph_char_number: int,
                         paragraph_list: List[ParagraphPipelineModel],
                         no_references_setting: Dict):
        if paragraph_list is None or len(paragraph_list) == 0:
            if no_references_setting.get('status') == 'ai_questioning':
                return HumanMessage(
                    content=no_references_setting.get('value').replace('{question}', problem))
            else:
                return HumanMessage(content=prompt.replace('{data}', "").replace('{question}', problem))
        temp_len = 0
        data_list = []
        for p in paragraph_list:
            content = f"{p.title}:{p.content}"
            temp_len += len(content)
            if temp_len > max_paragraph_char_number:
                row_data = content[0:max_paragraph_char_number - temp_len]
                data_list.append(f"<data>{row_data}</data>")
                break
            else:
                data_list.append(f"<data>{content}</data>")
        data = "\n".join(data_list)
        return HumanMessage(content=prompt.replace('{data}', data).replace('{question}', problem))

    def get_details(self, manage, **kwargs):
        return {
            'status': self.status,
            'err_message': self.err_message,
            'step_type': 'generate_human_message',
        }
