"""Only own pure checks and mocked sockets; does not launch the preflight."""
import errno
import socket
import unittest
from unittest.mock import patch
from python_runtime_preflight import version_at_least, readonly_mount, denied_connect


class RuntimeChecks(unittest.TestCase):
    def test_glibc_floor(self):
        self.assertTrue(version_at_least('glibc 2.36', [2, 28]))
        self.assertFalse(version_at_least('glibc 2.27', [2, 28]))
        self.assertFalse(version_at_least('unknown', [2, 28]))

    def test_mount_flags_required(self):
        self.assertTrue(readonly_mount('1 2 3:4 / /work ro,relatime - ext4 x rw', '/work'))
        self.assertFalse(readonly_mount('1 2 3:4 / /work rw,relatime - ext4 x rw', '/work'))
        self.assertFalse(readonly_mount('1 2 3:4 / /other ro - ext4 x rw', '/work'))

    def test_network_denials_are_conclusive(self):
        with patch('python_runtime_preflight.socket.socket') as factory:
            candidate = factory.return_value.__enter__.return_value
            for error, expected in [(socket.timeout(), False),
                                    (OSError(errno.ECONNREFUSED, 'refused'), False),
                                    (OSError(errno.ENETUNREACH, 'unreachable'), True)]:
                candidate.connect.side_effect = error
                self.assertEqual(denied_connect(('1.1.1.1', 443))[0], expected)


if __name__ == '__main__': unittest.main()
