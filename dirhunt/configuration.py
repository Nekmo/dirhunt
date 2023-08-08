from dataclasses import dataclass, field
from typing import TypedDict, List, Optional, Dict


class ConfigurationDict(TypedDict):
    """Configuration dict for Dirhunt. The keys are the same as the
    command line arguments of Dirhunt. See the management.py file for more
    information.
    """

    urls: List[str]
    threads: int
    exclude_flags: List[str]
    include_flags: List[str]
    interesting_extensions: List[str]
    interesting_files: List[str]
    interesting_keywords: List[str]
    stdout_flags: List[str]
    progress_enabled: bool
    timeout: int
    max_depth: int
    not_follow_subdomains: bool
    exclude_sources: List[str]
    proxies: List[str]
    delay: int
    not_allow_redirects: bool
    limit: int
    to_file: Optional[str]
    user_agent: Optional[str]
    cookies: Dict[str, str]
    headers: Dict[str, str]


@dataclass
class Configuration:
    """Configuration class for Dirhunt. The keys are the same as the ConfigurationDict
    class.
    """

    urls: List[str] = field(default_factory=list)
    threads: int = 10
    exclude_flags: List[str] = field(default_factory=list)
    include_flags: List[str] = field(default_factory=list)
    interesting_extensions: List[str] = field(default_factory=list)
    interesting_files: List[str] = field(default_factory=list)
    interesting_keywords: List[str] = field(default_factory=list)
    stdout_flags: List[str] = field(default_factory=list)
    progress_enabled: bool = True
    timeout: int = 10
    max_depth: int = 3
    not_follow_subdomains: bool = False
    exclude_sources: List[str] = field(default_factory=list)
    proxies: List[str] = field(default_factory=list)
    delay: int = 0
    not_allow_redirects: bool = False
    limit: int = 1000
    to_file: Optional[str] = None
    user_agent: Optional[str] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
