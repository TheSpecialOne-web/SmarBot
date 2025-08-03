from ipaddress import ip_address

import pytest

from api.domain.models.tenant import AllowedIP, AllowedIPs
from api.libs.exceptions import BadRequest


class TestAllowedIPs:
    def test_allowed_ips_valid_cidr(self):
        # 有効な CIDR を含む AllowedIPs インスタンスの作成
        allowed_ips = AllowedIPs(
            [
                AllowedIP(cidr="192.168.1.0/24"),
                AllowedIP(cidr="10.0.0.0/8"),
            ]
        )

        # 含まれるべき IP アドレス
        assert ip_address("192.168.1.1") in allowed_ips
        assert ip_address("10.1.2.3") in allowed_ips

        # 含まれないべき IP アドレス
        assert ip_address("172.16.0.1") not in allowed_ips

    def test_allowed_ips_invalid_cidr(self):
        # 無効な CIDR 形式を持つ AllowedIPs インスタンスの作成を試みる
        with pytest.raises(BadRequest):
            AllowedIP(cidr="192.168.1.0/33")

    def test_allowed_ips_ipv6(self):
        # IPv6 アドレス範囲をテスト
        allowed_ips = AllowedIPs([AllowedIP(cidr="fd00::/8")])

        assert ip_address("fd00:abcd:ef01:2345:6789:abcd:ef01:2345") in allowed_ips
        assert ip_address("fe80::abcd:ef01:2345:6789") not in allowed_ips
