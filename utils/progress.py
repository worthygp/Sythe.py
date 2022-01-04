class Progress:
    def __init__(self, tasks: list = None):
        self.tasks = []
        self.msg = None

        if tasks:
            for task in tasks:
                self.add_task(task)

    def add_task(self, task):
        self.tasks.append(task)

    def update_task(self, task_num: int, new_task: str):
        self.tasks[task_num - 1] = new_task

    def show(self, ctx, current: int = 0, recreate: bool = False):
        pretty_print = []
        for i, task in enumerate(self.tasks, start=1):
            if current < 0:
                pretty_print.append(f"☑️ ~~{task}~~")
            elif i == current:
                pretty_print.append(f"⏳ **{task}**")
            elif i < current:
                pretty_print.append(f"☑️ ~~{task}~~")
            else:
                pretty_print.append(f"🔃 *{task}*")

        results = "\n".join(pretty_print)

        if recreate and self.msg:
            self.msg.delete()
            msg = ctx.send(results)
            self.msg = msg
        if self.msg:
            self.msg.edit(content=results)
        else:
            msg = ctx.send(results)
            self.msg = msg

        return self.msg
