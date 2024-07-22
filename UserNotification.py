class UserNotification(Notification):
    def __init__(self):
        pass
        # name;
        # text;
        # level; info, warning, critical ...
        # type; balanceN, successN...
        # is_ blur; по умолчанию None
        # is_inline; по умолчанию None
        # state;

    def __send(self):
        pass
    # отправка(tg_send)

    @property
    def send(self):
        pass
    # __send()

    def preparing(self):
        pass
        # есть blur, inline?

    def feedback(self) -> feedbackEnum:
        pass