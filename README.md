# Scraping Browser
A simple, Qt-Webengine powered web browser with built in functionality for basic scrapy webscraping support.

# Instructions
## Browser Tab
Enter any url into search bar and hit return or press the Go button. When the loading animation finishes it will be ready to parse in the Tools tab.

![Browser tab](readme_images/browser.png "Browser Example")

## Tools Tab
The tools tab contains various sections for parsing content of the page. The purpose of this tab is to make it easy to test queries and code for use in a scrapy spider.
> **NOTE:** This will use the **initial** html response. If additional requests, javascript, etc alter the page later this will not be taken into account.

It will load the initial html with an additional request using the `requests` package. When running a query it will create a selector object using `Selection` from the parsel package.

![Tools tab](readme_images/tools.png "Tools Example")

### Query Box
The query box lets you use [parsel](https://github.com/scrapy/parsel) compatible CSS queries to extract data from the page.

It returns results as though `selection.css('YOUR QUERY').getall()` was called.

If there are no results or there is an error in the query a dialogue will pop up informing you of the issue.

### Regex Box
This box lets you add a regular expression pattern to be used in addition to the previous css query. 

It returns results as though `selection.css('YOUR QUERY').re(r'YOUR REGEX')'` was called. This means that if you use groups it will only return the content within parenthesis.

### Function Box
This box lets you define additional python code that can run on the results of your query and regex. The code can be as long and complex as you want, including adding additional functions, classes etc.

The only requirement is you must include a function called `user_fun(results)` that returns a `list`. 

### Results Box

This table will list all the results, passed through the regex and function if defined.

## Source Tab

This tab contains the html source that is used in the Tools tab. You can use the text box to search for specific content.

![Source Tab](readme_images/source.png "Source Example")

## Notes Tab

This is just a plain text box. Content in here us not saved when you exit the app.