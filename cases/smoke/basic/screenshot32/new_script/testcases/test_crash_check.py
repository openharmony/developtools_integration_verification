import pytest


class Test:

    # @pytest.mark.parametrize('setup_teardown', [None], indirect=True)
    def test(self, device):
        crashes = device.hdc_shell('cd /data/log/faultlog/temp && grep "Process name" -rnw ./')
        assert 'foundation' not in crashes, 'foundation crash exist'
        assert 'render_service' not in crashes, 'render_service crash exist'
        assert 'appspawn' not in crashes, 'appspawn crash exist'
