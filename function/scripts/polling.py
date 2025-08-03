import time

from jobs.jobs import JOB_NAMES_TO_QUEUE_NAMES
from jobs.main import execute as execute_job
from jobs.queue_storage import peek_messages

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
                execute_job(
                    job_name=job_name,
                )
        time.sleep(10)


if __name__ == "__main__":
    main()
