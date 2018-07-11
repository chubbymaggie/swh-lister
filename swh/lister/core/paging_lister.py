# Copyright (C) 2015-2018 the Software Heritage developers
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import abc
import logging

from .lister_transports import SWHListerHttpTransport
from .lister_base import SWHListerBase


class SWHPagingLister(SWHListerBase):
    """Lister* intermediate class for any service that follows the simple
       pagination page pattern.

    - Client sends a request to list repositories starting from a
      given page identifier.

    - Client receives structured (json/xml/etc) response with
      information about a sequential series of repositories (per page)
      starting from a given index. And, if available, some indication
      of the next page index for fetching the remaining repository
      data.

    See :class:`swh.lister.core.lister_base.SWHListerBase` for more
    details.

    This class cannot be instantiated. To create a new Lister for a
    source code listing service that follows the model described
    above, you must subclass this class. Then provide the required
    overrides in addition to any unmet implementation/override
    requirements of this class's base (see parent class and member
    docstrings for details).

    Required Overrides::

        def get_next_target_from_response

    """
    @abc.abstractmethod
    def get_next_target_from_response(self, response):
        """Find the next server endpoint page given the entire response.

        Implementation of this method depends on the server API spec
        and the shape of the network response object returned by the
        transport_request method.

        For example, some api can use the headers links to provide the
        next page.

        Args:
            response (transport response): response page from the server

        Returns:
            index of next page, possibly extracted from a next href url

        """
        pass

    @abc.abstractmethod
    def get_pages_information(self):
        """Find the total number of pages.

        Implementation of this method depends on the server API spec
        and the shape of the network response object returned by the
        transport_request method.

        For example, some api can use dedicated headers:
        - x-total-pages to provide the total number of pages
        - x-total to provide the total number of repositories
        - x-per-page to provide the number of elements per page

        Returns:
            tuple (total number of repositories, total number of
            pages, per_page)

        """
        pass

    # You probably don't need to override anything below this line.

    def run(self, min_index=None, max_index=None):
        """Main entry function. Sequentially fetches repository data from the
           service according to the basic outline in the class
           docstring. Continually fetching sublists until either there
           is no next index reference given or the given next index is
           greater than the desired max_index.

        Args:
            min_index (indexable type): optional index to start from
            max_index (indexable type): optional index to stop at

        Returns:
            nothing

        """
        index = min_index or ''
        loop_count = 0

        self.min_index = min_index
        self.max_index = max_index

        while self.is_within_bounds(index, self.min_index, self.max_index):
            logging.info('listing repos starting at %s' % index)

            response, injected_repos = self.ingest_data(index)
            next_index = self.get_next_target_from_response(response)

            # termination condition

            if (next_index is None) or (next_index == index):
                logging.info('stopping after index %s, no next link found' %
                             index)
                break
            else:
                index = next_index

            loop_count += 1
            if loop_count == 20:
                logging.info('flushing updates')
                loop_count = 0
                self.db_session.commit()
                self.db_session = self.mk_session()

        self.db_session.commit()
        self.db_session = self.mk_session()


class SWHPagingHttpLister(SWHListerHttpTransport, SWHPagingLister):
    """Convenience class for ensuring right lookup and init order when
       combining SWHPagingLister and SWHListerHttpTransport.

    """
    def __init__(self, api_baseurl=None, override_config=None):
        SWHListerHttpTransport.__init__(self, api_baseurl=api_baseurl)
        SWHPagingLister.__init__(self, override_config=override_config)