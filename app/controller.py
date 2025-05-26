from app.models import Project, LiteraryWork

def get_works():
    works = []
    works.append(get_tall_tales())
    works.append(get_the_outsider())
    return works


def get_projects():
    projects = []
    projects.append(get_eh_radio_logger_project())
    projects.append(get_casino_project())
    projects.append(get_hickoxyz_project())
    projects.append(get_teetime_booker_project())
    projects.append(get_ehlabs_project())
    projects.append(get_vimdeploy())
    projects.append(get_eshcript())
    return projects


def get_tall_tales():
    work = LiteraryWork(title="Tall Tales", date="June, 2019")
    desc = (
        "A collection of short stories "
        "including Sunset With Savannah, Loathing Las Vegas, and more. Free to download "
        "in PDF, ePub (Apple Books) and MOBI (Kindle) formats."
    )
    work.append_description(desc)
    work.add_download(
        "magnet:?xt=urn:btih:3fed609a1bfc8a0564a9388b0280db9659fbd300&dn=Tall%20Tales&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce"
    )
    return work


def get_the_outsider():
    work = LiteraryWork(title="The Outsider", date="September, 2019")
    desc = (
        "A novella loosely based around events during the year 2016 which "
        "tells the story of a time, a place, and a generation. "
        "Free to download in PDF, ePub (Apple Books) and MOBI (Kindle) formats."
    )
    work.append_description(desc)
    work.add_download(
        "magnet:?xt=urn:btih:3a807307ecc8da5b328ff684fa1a11d8d387e4a9&dn=The%20Outsider&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce"
    )
    return work

def get_ehlabs_project():
    project = Project(
        title="ehLabs",
        tagline="an experimental social media application and content management system",
        date="October, 2015",
        link="https://www.ehlabs.net"
    )

    desc = (
        "ehLabs is a catch-all for many of my personal projects. It contains several applications:"
        "<br>"
        "- real-time chat app"
        "<br>"
        "- blogging platform with backups into IPFS"
        "<br>"
        "- file hosting application with backups into IPFS and encryption capabilities"
        "<br>"
        "- news aggregator"
        "<br>"
        "- issue tracker"
        "<br>"
        "- public API"
        "<br>"
        "<br>"
        "ehLabs is currently invite only."
        "<br>"
        "ehLabs is closed source software."
    )

    project.append_description(desc)

    return project

def get_eh_radio_logger_project():
    project = Project(
        title="eh Radio Logger",
        tagline="a ham radio logging mobile app",
        date="May, 2025",
    )
    desc = ("eh Radio Logger is a simple amateur radio logging application for iOS. It has large, chunky buttons and is designed for use with one hand in the field when doing POTA or SOTA operations. "
            "It is written in Typescript and uses the React Native framework. "
            "<br>"
            "eh Radio Logger is closed source software. Download it on the Apple App Store using the link below.")
    project.append_description(desc)
    project.add_download("https://apps.apple.com/us/app/eh-radio-logger/id6744907119?itscg=30200&itsct=apps_box_link&mttnsubad=6744907119")
    return project

def get_casino_project():
    project = Project(
        title="casino",
        tagline="a video poker simulator",
        date="October, 2021",
        github="https://github.com/ehickox/casino"
    )

    desc = ("Casino is a python3 PyQT desktop application designed to simulate a video poker machine. It was designed to be deployed on a touch screen + Raspberry Pi. It uses the NIST randomness beacon when shuffling the cards. This was the last personal project I did before the LLM revolution changed software development. Some time later, I extended this application's functionality to include blackjack nearly entirely using LLMs.")
    
    project.append_description(desc)
    project.add_license("NCSA")
    return project

def get_hickoxyz_project():
    project = Project(
        title="hickoxyz",
        tagline="The personal website of Eli Hickox",
        date="March, 2015",
        github="https://github.com/ehickox/hickoxyz",
    )

    desc = (
        "hickoxyz is the repo name for the website you are viewing right now. It is a python3 Flask web app."
        "<br>"
        "The front end is custom and frameworkless. The CSS and (minimal) Javascript are bespoke. The navbar and slideshow components were written from scratch."
        "<br>"
        "As a design principle, I tried to use as little Javascript as possible to accomplish what I wanted."
    )

    project.append_description(desc)
    project.add_license("NCSA")

    return project

def get_teetime_booker_project():
    project = Project(
        title="teetime_booker",
        tagline="a script I used to book my favorite golf teetime",
        date="April, 2016",
        github="https://github.com/ehickox/teetime_booker",
    )

    desc = (
        "teetime_booker was a little python script I wrote to book my favorite golf teetime at a local course."
        "<br>"
        "I'm pretty sure this script is defunct and no longer works. Nevertheless it is my most-starred and most-forked repo on Github, so I've included it in this collection."
    )

    project.append_description(desc)
    project.add_license("MIT")

    return project

def get_vimdeploy():
    project = Project(
        title="vimdeploy",
        tagline="Quickly and easily deploy my favorite Vim configuration",
        date="February, 2015",
        github="https://github.com/ehickox/vimdeploy",
    )

    desc = (
        "Vimdeploy is a script that will set you up with my favorite vim configuration "
        "extremely quickly. To install, follow the instructions below:<br>"
        "<br>"
        "Optional: Back up your existing .vimrc file:<br>"
        "<samp>$ mv ~/.vimrc ~/.vimrc-old</samp><br>"
        "<br>"
        "1. Click the download link below and unzip the file.<br>"
        "<br>"
        "2. Change directories to the unzipped folder: <samp>$ cd 'PATH/TO/FOLDER'</samp><br>"
        "<br>"
        "3. Run <samp>$ ./deploy.sh</samp><br>"
        "NOTE: If that doesn't work, try running as root with: <br>"
        "<samp>$ sudo ./deploy.sh</samp> "
        "or make the script executable with: "
        "<samp>$ chmod u+x deploy.sh</samp><br>"
        "<br>"
        "4. Replace your vimrc file:<br>"
        "<samp>$ mv .vimrc ~/.vimrc</samp>"
    )

    project.append_description(desc)
    project.add_download("https://github.com/ehickox/vimdeploy/archive/master.zip")
    project.add_license("NCSA")

    return project


def get_eshcript():
    project = Project(
        title="ESHcript",
        tagline="An experimental Lisp programming language",
        date="April, 2014",
        github="https://github.com/ehickox/eshcript",
        download="https://github.com/ehickox/eshcript/archive/master.zip",
    )

    desc = (
        "ESHcript is an (incomplete) interpreted Lisp programming language developed by Eli "
        "S. Hickox, hence the name 'ESHcript'. This is not intended to be a full-scale, "
        "production level, programming language. A language is only as good as the library "
        "that surounds it. This is just a personal pet project that I have been tinkering "
        "with for a while. I mostly started this project as a way to learn C as well as a "
        "way to learn how programming languages are constructed.<br>"
        "<br>"
        "Makes use of the <a href='https://github.com/orangeduck/mpc'>mpc Parser Combinator "
        "Library</a> for C.<br>"
        "<br>"
        "If you'd like to try out ESHcript, keep in mind, it is Turing Incomplete and "
        "currently only supports basic arithmetic operations such as add, subtract, multiply, "
        "divide, min, max, modular arithmetic, and power. Data structures currently supported "
        "are limited to lists.<br>"
        "<br>"
        "To install, click on the download link below, unzip the file, and change directories "
        "to the unzipped location. Then run:<br>"
        "<samp>$ cc -std=c99 -Wall prompt.c mpc.c -ledit -lm -o prompt</samp>"
        "<br>"
        "Now you should be able to run: <samp>$ ./prompt</samp>. A shell similar to the Python "
        " Interactive Shell should start."
    )

    project.append_description(desc)
    project.add_license("MIT")
    return project
