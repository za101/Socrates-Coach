class IOBase():
    def get_user_input(self):
        pass

    def deliver_output(self, content):
        pass

class CliIO(IOBase):
    def get_user_input(self):
        user_input = input(f'>> ')
        return user_input

    def deliver_output(self, content):
        print(content + "\n")