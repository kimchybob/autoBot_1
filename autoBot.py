import json
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv

load_dotenv()
emailAddress = os.getenv('EMAIL')
password = os.getenv('PASSWD')


chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('excludeSwitches',['enable-automation'])
prefs = {'credentials_enable_service':False,'profile.password_manager_enabled':False}
chrome_options.add_experimental_option('prefs',prefs)
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

quickDriver = webdriver.Chrome()

foundApplied = False
baseURL = "https://www.seek.com.au/jobs-in-information-communication-technology?salaryrange=90000-&salarytype=annual&sortmode=ListedDate&subclassification=6285%2C6287%2C6302%2C6303%2C6290&worktype=242%2C244&page="
blockedKeywords = ['AEM ', '365', 'Salesforce', 'BI ', 'SAP ','Net ', 'C#', 'lead', 'Business', 'C++','EPM', 'cyber', 'ServiceNow', 'Graduate',
                   'Trainer','Coordinator','Training','Dynamics','PeopleSoft','Sharepoint','CDM','Designer', 'bpm', 'ios', 'ops',
                   'support','process', 'intern','data','Analyst', 'pega',
                   'D365','CRM','PHP','Officer','Golang','Manager','ETL','Onboarding','Principal','Director', 'servicenow']

def login(driver):
    try:
        # Attempt to find the login element
        loginEntry = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[3]/div[2]/div/div/div[1]/div[2]/div[1]/div/div/div/div/div/a')
        loginEntry.click()

        emailField = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailAddress"]')))

        pwdField = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))

        emailField.send_keys(emailAddress)

        pwdField.send_keys(password)

        loginButton = (driver.find_element(By.XPATH, '//*[@id="signin_seekanz"]/div/div[4]/div/div[1]/button'))
        loginButton.click()

        time.sleep(5)

    except NoSuchElementException:
        # Handle the case when the element is not found
        pass

def creatNewTab(drive):
    drive.execute_script("window.open('', '_blank');")
    # Switch to the new tab
    drive.switch_to.window(drive.window_handles[-1])

def findElementsUntilApplied(elements):
    output= []
    count = 0
    for element in elements:
        # output.append(element.find_element(By.XPATH, './/a[contains(@id,"job-title")]'))

        try:
            # Try to find the specific element within the current element
            element.find_element(By.XPATH, './/span[@aria-hidden="true" and contains(text(), "Applied")]')
            count += 1
            if count > 1:
                global foundApplied
                foundApplied = True
                # If found, break out of the loop
                break

        except NoSuchElementException:
            output.append(element.find_element(By.XPATH, './/a[contains(@id,"job-title")]'))
    return output

def getJobs(driver):

    page = 1
    dateRange = "&daterange=17"
    unappliedURL = []

    while not foundApplied:
        driver.get(baseURL + str(page) + dateRange)

        login(driver)

        elements = WebDriverWait(driver, 30).until(EC.visibility_of_all_elements_located((By.XPATH, '//article[contains(@data-card-type, "JobCard")]')))

        excludedElements = findElementsUntilApplied(elements[2:])

        for element in excludedElements:
            url = element.get_attribute('href')
            if not any(keyword.lower() in element.text.lower() for keyword in blockedKeywords):
                unappliedURL.append(url)
                toFile(element.text + ' url is: ' + url, 'unappliedURL.txt')
            else:
                toFile(element.text + ': ' + url, 'blockedJob.txt')
        page += 1

    print(len(unappliedURL))
    return unappliedURL

def apply(title):

    login(quickDriver)

    try:
        applied = quickDriver.find_element(By.XPATH,'//span[contains(text(), "You\'ve applied on ")]')
        if applied:
            return False
    except NoSuchElementException:
        pass


    # blockStatus = ["citizen","clearance","Citizen","Clearance"]
    # citizen = quickDriver.find_element_by_xpath("//*[contains(text(), '{blockStatus}')]")
    # if citizen:
    #     return False

    curUrl = quickDriver.current_url

    try:
        quickApply = WebDriverWait(quickDriver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@data-automation, "job-detail-apply")]')))

        if quickApply.text != "Quick apply":
            toFile(title + '  ' + '\'' + curUrl + '\'', 'external.py')
            return False

        quickApply.click()

        while True:
            try:
                elements = quickDriver.find_element(By.XPATH,'//*[@id="errorPanel"]')
                if elements:
                    return True
            except NoSuchElementException:
                pass
            try:
                next = WebDriverWait(quickDriver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//button[contains(@data-testid, "continue-button")]')))

                next.click()
            except StaleElementReferenceException as sa:
                continue
            except Exception as e:
                print(e)
                break

        submit = WebDriverWait(quickDriver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(@data-testid, "review-submit-application")]')))
        submit.click()
        toFile(curUrl, 'submit.txt')
        return False
    except Exception as e:
        print(e)
        return True

def traverse(lines):
    newTab = False
    index = 0

    for line in lines:
        print(index)
        index += 1

        if newTab:
            creatNewTab(quickDriver)

        quickDriver.get(line.split('url is: ')[1])

        newTab = apply(line.split('url is: ')[0])



def main():
    getJobs(quickDriver)
    # list = readFile()
    # traverse(list)

def toFile(item, path):
    # Open the file for writing
    with open(path, 'a') as file:
        file.write(f"{item}\n")

def readFile():
    with open('unappliedURL.txt', 'r') as file:
        lines = file.readlines()
    # Remove leading and trailing whitespaces, and create a list
    # string_list = [line.split('url is: ')[1] for line in lines]

    return lines


main()