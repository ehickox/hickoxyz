from models import Project
def get_projects():
    projects = []
    projects.append(get_bitraider())
    projects.append(get_vimdeploy())
    projects.append(get_pebble_bitcoin_wallet())
    return projects

def get_bitraider():
    bitraider = Project(title="bitraider", tagline="A Bitcoin Algorithmic Trading Framework",
                        date="May, 2015",
                        github="https://github.com/ehickox2012/bitraider",
                        link="http://ehickox2012.github.io/bitraider")
    
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
                      github="https://github.com/ehickox2012/BitcoinWallet")
    
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
    project.add_download("https://github.com/ehickox2012/BitcoinWallet/archive/master.zip")

    return project

def get_vimdeploy():
    project = Project(title="vimdeploy",
                      tagline="Quickly and easily deploy my favorite Vim configuration",
                      date="February, 2015",
                      github="https://github.com/ehickox2012/vimdeploy")

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
    project.add_download("https://github.com/ehickox2012/vimdeploy/archive/master.zip")

    return project
