# Copyright 2021 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from typing import Any, Dict, Optional, Tuple

import attr
from synapse.module_api import EventBase, ModuleApi

logger = logging.getLogger(__name__)
ACCOUNT_DATA_DIRECT_MESSAGE_LIST = "m.direct"


@attr.s(auto_attribs=True, frozen=True)
class InviteAutoAddAwTeamConfig:
    worker_to_run_on: Optional[str] = None


class InviteAutoAddAwTeam:
    def __init__(self, config: InviteAutoAddAwTeamConfig, api: ModuleApi):
        # Keep a reference to the Module API.
        self._api = api
        self._config = config

        should_run_on_this_worker = config.worker_to_run_on == self._api.worker_name

        if not should_run_on_this_worker:
            logger.info(
                "Not accepting invites on this worker (configured: %r, here: %r)",
                config.worker_to_run_on,
                self._api.worker_name,
            )
            return

        logger.info(
            "Accepting invites on this worker (here: %r)", self._api.worker_name
        )

        # Register the callback.
        self._api.register_third_party_rules_callbacks(
            on_new_event=self.on_new_event,
        )

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> InviteAutoAddAwTeamConfig:
        """Checks that the required fields are present and at a correct value, and
        instantiates a InviteAutoAddAwTeamConfig.

        Args:
            config: The raw configuration dict.

        Returns:
            A InviteAutoAddAwTeamConfig generated from this configuration
        """


        worker_to_run_on = config.get("worker_to_run_on", None)

        return InviteAutoAddAwTeamConfig(
            worker_to_run_on=worker_to_run_on,
        )

    async def on_new_event(self, event: EventBase, *args: Any) -> None:
        """Listens for new events, and if the event is an invite for a local user then
        automatically accepts it.

        Args:
            event: The incoming event.
        """
        # Check if the event is an invite for a local user.
        
        if (
            event.type == "m.room.member"
            and event.is_state()
            and event.membership == "join"
            and self._api.is_mine(event.state_key)
        ):
            # add to appwrite team
            logger.debug(
                "NEW EVENT FROM MODULE"
            )
            

            room_id = event.room_id
            user_id = event.state_key

            logger.debug(room_id)
            logger.debug(user_id)

