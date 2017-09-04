# Copyright (C) 2017 the Software Heritage developers
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.lister.core.tasks import (IndexingDiscoveryListerTask,
                                   IndexingRangeListerTask,
                                   IndexingRefreshListerTask, ListerTaskBase)

from .lister import GitHubLister


class GitHubListerTask(ListerTaskBase):
    def new_lister(self):
        return GitHubLister(lister_name='github.com',
                            api_baseurl='https://github.com')


class IncrementalGitHubLister(GitHubListerTask, IndexingDiscoveryListerTask):
    task_queue = 'swh_lister_github_discover'


class RangeGitHubLister(GitHubListerTask, IndexingRangeListerTask):
    task_queue = 'swh_lister_github_refresh'


class FullGitHubRelister(GitHubListerTask, IndexingRefreshListerTask):
    task_queue = 'swh_lister_github_refresh'