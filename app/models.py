class Project():

    def __init__(self, title="", tagline="", date="", description="", github="",
                 link="", download="", copywrite="2015 Eli Hickox"):
        self.title = title
        self.tagline = tagline
        self.date = date
        self.description = description
        self.github = github
        self.link = link
        self.download = download
        self.copywrite= copywrite

    def append_description(self, text=""):
        if text != "":
            self.description += text

    def add_download(self, text=""):
        if text != "":
            self.download = text

    def add_license(self, text=""):
        if text != "":
            self.copywrite += " License: "+text
