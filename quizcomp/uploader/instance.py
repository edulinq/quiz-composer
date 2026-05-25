import typing

class CanvasInstanceInfo:
    """ Info on how to connect to a Canvas instance. """

    def __init__(self, base_url: str, course_id: str, token: str, testing: bool = False) -> None:
        self.base_url: str = base_url
        """ URL for the target Canvas server. """

        self.course_id: str = course_id
        """ ID of the target Canvas course. """

        self.token: str = token
        """ Canvas authentication token. """

        self.context: typing.Dict[str, typing.Any] = {}
        """ Context information. """

        self.testing: bool = testing
        """ Indicates that this is an instance used in testing and should not try to be used for a real server. """

    def base_headers(self) -> typing.Dict[str, str]:
        """ Get standard Canvas headers. """

        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json+canvas-string-ids",
        }
