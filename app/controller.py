from models import Project

def get_projects():
    projects = []
    projects.append(get_bitraider())
    projects.append(get_bitscramblr())
    projects.append(get_vimdeploy())
    projects.append(get_pebble_bitcoin_wallet())
    projects.append(get_eshcript())
    return projects

def get_bitscramblr():
    bitscramblr = Project(title="bitscramblr", tagline="Bitcoin transaction anonymization",
                          date="April, 2015", github="https://github.com/ehickox/bitscramblr",
                          link="https://www.academia.edu/16612889/Bitcoin_Transaction_Anonymization_Through_Randomized_Dynamic_Transactions")

    desc = ("Bitscramblr is an application that allows you to send Bitcoin anonymously. "
            "It differs from many mixing services in existence in that a transaction will "
            "not be sent until adequately sized inputs are available from another source. "
            "Basically what this means is: there is no path from a transaction's origin to its destination."
            "For a more detailed overview of the Graph Theory principles that make Bitscramblr work, "
            "click on the link below to read my research paper. A proof of concept implementation can be "
            "found at the GitHub link provided.")
    
    bitscramblr.append_description(desc)
    bitscramblr.add_licence("Apache 2")

def get_bitraider():
    bitraider = Project(title="bitraider", tagline="A Bitcoin Algorithmic Trading Framework",
                        date="May, 2015",
                        github="https://github.com/ehickox/bitraider",
                        link="http://ehickox.github.io/bitraider")
    
    desc = ("Bitraider is a collection of tools for algorithmic bitcoin "
           "trading in Python. Bitraider includes an Abstract Exchange "
           "that allows it to be flexible as Bitcoin Exchanges come and go. "
           "Currently, it uses CoinbaseExchange. Bitraider allows users to "
           "create plug-n-play strategies using its Abstract Strategy. "
           "Users can then backtest created strategies on historical data, "
           "or optimize constant values in their strategies using cross-fold "
           "validation before using Bitraider to perform live trades. For "
           "more information on how to get started with bitraider, click on "
           " the link below.")

    bitraider.append_description(desc)
    bitraider.add_license("MIT")
    return bitraider

def get_pebble_bitcoin_wallet():
    project = Project(title="BitcoinWallet",
                      tagline="A Pebble watch face that displays a Bitcoin address QR code",
                      date="April, 2014",
                      github="https://github.com/ehickox/BitcoinWallet")
    
    desc = ("A Pebble watch face that displays an image of your Bitcoin (or other alt coin) "
            "wallet's QR code. Imagine if a friend wanted to send you money... With this app, "
            "all you need to do is switch your watchface and have your friend scan your watch "
            " with his or her phone.<br>"
            "<br>"
            "To install, click the download link below, then follow these instructions:<br>"
            "<br>"
            "In 'resources/images/' there is a .png file called 'wallet.png'. To adapt this "
            "watch face for your own purposes, all you need to do is replace the 'wallet.png' "
            "with a PNG of your own image, scaled to 140x140 pixels. From there, run: <br>"
            "<br>"
            "<samp>$ pebble build</samp><br> "
            "<samp>$ pebble install --phone 'IP ADDRESS OF YOUR PHONE'</samp>")
            
    project.append_description(desc)
    project.add_download("https://github.com/ehickox/BitcoinWallet/archive/master.zip")

    return project

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
