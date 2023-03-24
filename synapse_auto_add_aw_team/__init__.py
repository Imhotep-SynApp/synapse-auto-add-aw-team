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
import os
from typing import Any, Dict, Optional, Tuple
from appwrite.client import Client
from appwrite.services.teams import Teams
from appwrite.services.users import Users

import attr
from synapse.module_api import EventBase, ModuleApi

logger = logging.getLogger(__name__)
ACCOUNT_DATA_DIRECT_MESSAGE_LIST = "m.direct"


@attr.s(auto_attribs=True, frozen=True)
class InviteAutoAddAwTeamConfig:
    worker_to_run_on: Optional[str] = None
    appwrite_endpoint: str = None
    appwrite_api_key: str = None


class InviteAutoAddAwTeam:
    def __init__(self, config: InviteAutoAddAwTeamConfig, api: ModuleApi):
        # Keep a reference to the Module API.
        self._api = api
        self._config = config

        client = Client()

        (client
            .set_endpoint(config.appwrite_endpoint) # Your API Endpoint
            .set_project('synapp-messaging') # Your project ID
            .set_key(config.appwrite_api_key) # Your secret API key
        )

        self.teams = Teams(client)
        self.users = Users(client)

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
        
        appwrite_endpoint = os.environ.get('APPWRITE_ENDPOINT', None)
        appwrite_api_key = os.environ.get('APPWRITE_API_KEY', None)

        return InviteAutoAddAwTeamConfig(
            worker_to_run_on=worker_to_run_on,
            appwrite_endpoint=appwrite_endpoint,
            appwrite_api_key=appwrite_api_key,
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
            room_id: str = event.room_id
            room_id = room_id[1:].split(':')[0]
            user_id = event.state_key
            user_id = user_id[1:].split(':')[0]

            logger.debug("add {} to room {}".format(user_id, room_id))
            
            # if team not exist
            try:
                self.teams.get(room_id)
            except:
                self.teams.create(room_id, room_id)

            user = self.users.get(user_id)

            # add user_email to room_id

            self.teams.create_membership(room_id, user['email'], [], 'http://localhost')

        if (
            event.type == "m.room.member"
            and event.is_state()
            and event.membership == "invite"
            and self._api.is_mine(event.state_key)
        ):
           await self._api.update_room_membership(
                    sender=event.state_key,
                    target=event.state_key,
                    room_id=event.room_id,
                    new_membership="join",
                )


            
            
            

