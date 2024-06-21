import pytest


class TestCrashCheck:

    @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, setup_teardown, device):
        crashes = device.hdc_shell('cd /data/log/faultlog/temp && grep "Process name" -rnw ./')
        assert 'foundation' not in crashes, '检查到有 foundation crash'
        assert 'render_service' not in crashes, '检查到有 render_service crash'
        assert 'appspawn' not in crashes, '检查到有 appspawn crash'
