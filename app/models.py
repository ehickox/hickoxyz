class Project():

    def __init__(self, title="", tagline="", date="", description="", github="",
                 link="", download="", copywrite="Eli Hickox"):
        self.title = title
        self.tagline = tagline
        self.date = date
        self.description = description
        self.github = github
        self.link = link
        self.download = download
        self.copywrite = copywrite

    def append_description(self, text=""):
        if text != "":
            self.description += text

    def add_download(self, text=""):
        if text != "":
            self.download = text

    def add_license(self, text=""):
        if text != "":
            self.copywrite += " License: "+text

class LiteraryWork():

    def __init__(self, title="", date="", description="", download="", copywrite="Eli Hickox - All Rights Reserved"):
        self.title = title
        self.date = date
        self.description = description
        self.copywrite = copywrite

    def append_description(self, text=""):
        if text != "":
            self.description += text

    def add_download(self, text=""):
        if text != "":
            self.download = text

    def add_license(self, text=""):
        if text != "":
            self.copywrite = text
