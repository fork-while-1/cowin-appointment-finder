# cowin-appointment-finder

User config : these are things the user would have to input to tailor the app towards them

1) PINCODES = this is the list of pincodes of hospitals the user is interested in getting an appointment at

2) MOBILE = the mobile number registered with the cowin website

3) REFERENCE_ID = the reference ID assigned to the user whose appointment we want to book, can be obtained through the cowin website portal on loggin in

4) BROWSER = the command to open your favorite browser though the terminal/command prompt. ("start chrome" is Windows specific, for linux you can use "google-chrome"/"firefox")

5) CAPTCHA_PATH = this is the full path of the place where you put this python app (which is the same directory the app will use to store the captcha)

Other config: may or may not be changed, up to the user

1) SLEEP_INTERVAL = the amount of time the app waits before retrying the search for new appointments. Default value = 1.5 minutes (Note: don't set this to a very small number since sending too many requests in a short interval will lock you out of the website)


