import unittest

from scripts.m11_backup_restore_drill import docker_pg, validate_local_target


class BackupRestoreDrillTests(unittest.TestCase):
    def test_only_local_database_is_allowed(self):
        validate_local_target("telecom_ai_agent", "127.0.0.1", "5432")
        for args in (
            ("telecom_ai_agent", "db.example.com", "5432"),
            ("telecom-ai-agent", "127.0.0.1", "5432"),
            ("telecom_ai_agent", "localhost", "abc"),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate_local_target(*args)

    def test_password_is_not_passed_in_process_arguments(self):
        command = docker_pg("telecom-ai-postgres", "pg_dump", "telecom_ai_agent", "--format=custom")
        self.assertIn('PGPASSWORD="$POSTGRES_PASSWORD"', command[command.index("-c") + 1])
        self.assertNotIn("actual-secret", " ".join(command))
        self.assertEqual(command[-1], "telecom_ai_agent")

    def test_unsupported_command_rejected(self):
        with self.assertRaises(ValueError):
            docker_pg("telecom-ai-postgres", "rm", "telecom_ai_agent")

    def test_restore_passes_database_with_explicit_flag(self):
        command = docker_pg("telecom-ai-postgres", "pg_restore", "m11_restore_test", "--exit-on-error", interactive=True)
        self.assertIn(' -d "$db" ', command[command.index("-c") + 1])
        self.assertEqual(command[command.index("-c") + 3], "m11_restore_test")
        self.assertIn("-i", command)


if __name__ == "__main__":
    unittest.main()
