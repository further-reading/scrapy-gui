from cssselect.xpath import ExpressionError
from cssselect.parser import SelectorSyntaxError
import traceback
from . import errors


class Parser:
    def __init__(self, selector):
        self.selector = selector

    def do_query(self, css, selector, regex=None, function=None):
        try:
            results = self.selector.css(css)
        except (ExpressionError, SelectorSyntaxError) as e:
            message = f'Error parsing css query\n\n{e}'
            raise errors.QueryError(
                title='CSS Error',
                message=message,
                error_type='critical',
            )
        if not results:
            raise errors.QueryError(
                title='CSS Empty',
                message=f'No results for CSS Query\n{css}',
                error_type='info',
            )
        if regex:
            try:
                results = results.re(regex)
            except Exception as e:
                message = f'Error running regex\n\n{e}'
                raise errors.QueryError(
                    title='RegEx Error',
                    message=message,
                    error_type='critical',
                )
            if not results:
                raise errors.QueryError(
                    title='RegEX Empty',
                    message=f'No results for Regular Expression\n{regex}',
                    error_type='info',
                )

        else:
            results = results.getall()

        if function:
            results = self.use_custom_function(results, function, selector)
            if not results:
                raise errors.QueryError(
                    title='Function Empty',
                    message=f'No results when using function\n\n{function}',
                    error_type='critical',
                )
        return results

    def use_custom_function(self, results, function, selector):
        if 'def user_fun(results, selector):' not in function:
            message = f'Custom function needs to be named "user_fun" and have "results" and "selector" as arguments'
            raise errors.QueryError(
                title='Function Error',
                message=message,
                error_type='critical',
            )

        try:
            exec(function, globals())
            results = user_fun(results, selector)
        except Exception as e:
            message = f'Error running custom function\n\n{type(e).__name__}: {e.args}'
            message += f'\n\n{traceback.format_exc()}'
            raise errors.QueryError(
                title='Function Error',
                message=message,
                error_type='critical',
            )

        return results