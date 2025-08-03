from datetime import datetime

from pydantic import RootModel
import pytz


class CreatedAt(RootModel[datetime]):
    root: datetime

    def jst_formatted(self) -> str:
        jst_time = self.root.astimezone(pytz.timezone("Asia/Tokyo"))
        # 日時を「年-月-日 時:分」の形式でフォーマット
        return jst_time.strftime("%Y-%m-%d %H:%M")
