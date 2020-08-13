from app.models import Project, LiteraryWork
import dateutil.parser
import datetime
import json

def get_last_years_commits():
    data = None
    weekly_totals = []
    quarterly_totals = []
    quarterly_avgs = []
    with open('app/historic_commits.json') as data_file:
        data = json.load(data_file)

    dates_list = []
    for datestr in data.keys():
        if "2011" not in datestr and "2012" not in datestr and "2013" not in datestr:
            dates_list.append(dateutil.parser.parse(datestr))

    dates_list.sort()
    quarter_ends = ['03','06','09','12']
    days_in_year_month = {} # {'2016-01': [5, 8, 9, ...]}
    quarterly_total = 0
    num_weeks_per_quarter = 0
    quarter_idx = 0
    q_num = 1
    quarter_calculated = {}
    for dat in dates_list:
        key = str(dat)
        value = data[key]
        datestr = key.split(' ')[0]
        year = datestr.split('-')[0]
        month = datestr.split('-')[1]
        day = datestr.split('-')[2]
        if days_in_year_month.get(year+'-'+month, []) == []:
            days_in_year_month[year+'-'+month] = [int(day)]
        else:
            days_in_year_month.get(year+'-'+month).append(int(day))

    for dat in dates_list:
        key = str(dat)
        value = data[key]
        weekly_totals.append([key, value])
        quarterly_total += value
        num_weeks_per_quarter += 1
        datestr = key.split(' ')[0]
        year = datestr.split('-')[0]
        month = datestr.split('-')[1]
        day = datestr.split('-')[2]
        #print(datestr+' '+str(value))
        if month in quarter_ends and int(day) == max(days_in_year_month.get(year+'-'+month)):
            idx = 'Q'+str(q_num)+' '+year
            quarterly_totals.append([idx, quarterly_total])
            quarterly_avgs.append([idx, (float(quarterly_total)/12)])
            num_weeks_per_quarter = 0
            quarterly_total = 0
            quarter_calculated[month+' '+year] = True
            q_num += 1
            if q_num > 4:
                q_num = 1

    one_x = 0
    for avg in quarterly_avgs:
        if avg[1] != 0 and one_x == 0:
            one_x = avg[1]

    exes_list = []
    for avg in quarterly_avgs:
        exes_list.append([avg[0], avg[1]/float(one_x)])

    return weekly_totals, quarterly_totals, quarterly_avgs,exes_list

def get_works():
    works = []
    works.append(get_tall_tales())
    works.append(get_the_outsider())
    return works

def get_projects():
    projects = []
    projects.append(get_vimdeploy())
    projects.append(get_eshcript())
    return projects

def get_tall_tales():
    work = LiteraryWork(title="Tall Tales",
                        date="June, 2019")
    desc = ("A collection of short stories "
            "including Sunset With Savannah, Loathing Las Vegas, and more. Free to download "
            "in PDF, ePub (Apple Books) and MOBI (Kindle) formats.")
    work.append_description(desc)
    work.add_download("magnet:?xt=urn:btih:3fed609a1bfc8a0564a9388b0280db9659fbd300&dn=Tall%20Tales&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce")
    return work

def get_the_outsider():
    work = LiteraryWork(title="The Outsider",
                        date="September, 2019")
    desc = ("A novella loosely based around events during the year 2016 which "
            "tells the story of a time, a place, and a generation. "
            "Free to download in PDF, ePub (Apple Books) and MOBI (Kindle) formats.")
    work.append_description(desc)
    work.add_download("magnet:?xt=urn:btih:3a807307ecc8da5b328ff684fa1a11d8d387e4a9&dn=The%20Outsider&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce")
    return work

def get_vimdeploy():
    project = Project(title="vimdeploy",
                      tagline="Quickly and easily deploy my favorite Vim configuration",
                      date="February, 2015",
                      github="https://github.com/ehickox/vimdeploy")

    desc = ("Vimdeploy is a script that will set you up with my favorite vim configuration "
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
            "<samp>$ mv .vimrc ~/.vimrc</samp>")

    project.append_description(desc)
    project.add_download("https://github.com/ehickox/vimdeploy/archive/master.zip")

    return project

def get_eshcript():
    project = Project(title="eshcript", tagline="An experimental Lisp programming language",
                      date="April, 2014", github="https://github.com/ehickox/eshcript",
                      download="https://github.com/ehickox/eshcript/archive/master.zip")

    desc = ("ESHcript is an (incomplete) interpreted Lisp programming language developed by Eli "
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
            " Interactive Shell should start.")

    project.append_description(desc)
    project.add_license("MIT")
    return project
