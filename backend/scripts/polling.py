from dotenv import load_dotenv

load_dotenv(".env")

import time

from api.domain.models.job.job import JOB_NAMES_TO_QUEUE_NAMES
from api.jobs.jobs import execute_jobs
from api.jobs.queue_storage import peek_messages

queue_names = JOB_NAMES_TO_QUEUE_NAMES.values()


def main():
    # 10秒ごとにローカルのキューをポーリングしてジョブを実行する
    while True:
        print("Polling queues for messages")
        for queue_name in queue_names:
            messages = []
            try:
                messages = peek_messages(queue_name)
            except Exception as e:
                print(f"Error while peeking messages from {queue_name}: {e}")
                continue
            if len(messages) == 0:
                continue
            print(f"Found {len(messages)} messages in queue {queue_name}")
            for _ in messages:
                job_name = None
                for job, queue in JOB_NAMES_TO_QUEUE_NAMES.items():
                    if queue == queue_name:
                        job_name = job
                        break
                if job_name is None:
                    print(f"Job name not found for queue name {queue_name}")
                    continue

                try:
                    execute_jobs(job_name=job_name)
                except Exception:
                    # ジョブの実行中にエラーが発生した場合は、次のメッセージに進む
                    continue
        time.sleep(10)


if __name__ == "__main__":
    main()
