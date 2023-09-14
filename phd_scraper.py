import requests # for making HTTP Requests
from bs4 import BeautifulSoup # for parsing HTML content
import smtplib # for connecting to SMTP server (for sending mails)
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import logging


def send_mail(subject,message,config):
    #This function will send a mail with subject and containing message using the information in the config file.


    # read the necessary data from the config file
    username = config.get('Email','username') #from address
    psswrd = config.get('Email','psswrd') #password
    server = config.get('Email','server') #SMTP server
    port = config.get('Email','port') #SMTP port
    recipient = config.get('Email','recipient') # to address
    
    # Create MIME object 
    msg = MIMEMultipart() 
    msg['From'] = username
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(message,'plain'))
    try:
        smtp_connection = smtplib.SMTP(server,port)# Create connection object
        smtp_connection.starttls() # Connect to SMTP server
        smtp_connection.login(username, psswrd) # Login
        smtp_connection.sendmail(username,recipient,msg.as_string()) # Send message
        smtp_connection.quit() # Close connection
    except Exception as e:
        logging.error("Failed to send email. Got the following error: ",str(e))



def read_lines(path):
    with open(path, 'r') as file:
        lines =  [line.strip() for line in file.readlines()] # strip removes the trailing \n from the lines
    return lines

def remove_lines(path,remove_line_numbers):
    # read all lines
    with open(path, 'r') as file:
        lines = file.readlines()

    # only maintain lines not in the remove list
    new_lines = [line for i,line in enumerate(lines) if i not in remove_line_numbers]
    with open(path, 'w') as file:
        file.writelines(new_lines)



def check_calendar(url,phd_list):
    response = requests.get(url) # Fetch the calendar webpage
    if response.status_code == 200:
        # Succesfully fetched the PhD calendar
        soup = BeautifulSoup(response.content, 'html.parser') # Parse the webpage
        html_tables = soup.find_all("table") # 
        if len(html_tables) < 3:
            # The structure of the PhD calendar has changed. Send an e-mail to myself so I can modify the script.
            raise Exception("ERROR: Failed to locate the PhD calendar on the webpage.")
        calendar = html_tables[2] # Get third table on page
        rows = calendar.find_all("tr")  # Get all rows
        title_row = rows[0] # Get title row
        if title_row.find_all(recursive=False)[1].find().get_text() != "Naam":
            # The structure of the PhD calendar has changed. Send an e-mail to myself so I can modify the script.
            raise Exception("The structure of the PhD calendar has changed!")
        found = []
        found_pos = []
        for row in rows[1:]:
            name = row.find_all(recursive=False)[1].find().get_text().strip()
            try:
                pos = phd_list.index(name)
                found.append(name)
                found_pos.append(pos)
            except ValueError:
                pass
        return found,found_pos
    else:
        raise Exception("Failed to fetch the PhD calender webpage.")
        
        


if __name__ == "__main__":
    log_file = 'debug.log'
    logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
    )

    config = configparser.ConfigParser()
    config.read('config.ini')
    
    url = config.get('General','url') # URL of the PhD calendar of the Faculty of Engineering Sciences
    phd_list_path = config.get('General','phd_list_path')

    phd_list = read_lines(phd_list_path)
    
    try:
        found,found_pos = check_calendar(url,phd_list)
        if len(found) > 0:
            logging.info("Hurrah!!! One (or more) PhD student(s) on your watchlist are defending in the near future.")
            subject = "Upcoming NUMA defence"
            msg = "Dear Pieter,\n\nThe PhDScraper detected that a PhD student on your watchlist is defending in the near future. More specifically:\n\n{}\n\nwill defend in the near future. Check the PhD calendar at {} for more information.\n\nBest regards,\n\nPieter".format('\n'.join(found),url)
            send_mail(subject,msg,config)
            remove_lines(phd_list_path,found_pos)
        else:
            logging.info("What a pity. None of the PhD students on your watchlist are defending in the near future.")
    except Exception as e:
        logging.error(str(e))
        subject = "The PhDScraper ran into an issue"
        msg = "Hey Pieter,\n\nThe PhDScraper encountered an error. The error message reads: \n\n{}\n\nPlease go fix your code.\n\nBest regards,\n\nPieter".format(str(e))
        send_mail(subject,msg,config)


