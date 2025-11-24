from typing import Any, Dict, List, Text
from langdetect import detect

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

import sqlite3
import langdetect
from datetime import datetime

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # hard-coded balance for tutorial purposes. in production this
        # would be retrieved from a database or an API

        answer = tracker.latest_message.text
        print(answer)
        lang = langdetect.detect(answer)

        return [SlotSet("language", lang)]



class ActionCheckSufficientFunds(Action):
    def name(self) -> Text:
        return "action_check_sufficient_funds"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # hard-coded balance for tutorial purposes. in production this
        # would be retrieved from a database or an API
        balance = 1000
        transfer_amount = tracker.get_slot("amount")
        has_sufficient_funds = transfer_amount <= balance
        return [SlotSet("has_sufficient_funds", has_sufficient_funds)]

class ActionIdentifyCustomer(Action):
    def name(self) -> Text:
        return "action_identify_customer"
    # This function finds the contract ID given a customer ID.
    # If a contract is found, then the "contract_id" slot is set and
    # the "customer_is_identified" slot is set to True.
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        customer_id = tracker.get_slot("customer_id")
        print("customer_id: {0}".format(customer_id))

        contract_id = ""
        customer_identified = False
        conn = sqlite3.connect("db/SonnePur.db")
        mycur = conn.cursor()
        sql = """
            SELECT vertrag_id FROM vertraege WHERE kunde_id = ?;
        """
        mycur.execute(sql, (customer_id,))
        record = mycur.fetchone()
        if record:
            contract_id = record[0]
            customer_identified = True
        print("contract_id = {0}".format(contract_id))
        return [SlotSet("contract_id", contract_id), SlotSet("customer_is_identified", customer_identified)]

class ActionGetMeterReading(Action):
    def name(self) -> Text:
        return "action_get_current_meter_reading"
    # This function, given a contract ID, finds the current meter reading on this contract
    # along with the last date the meter was read.
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        contract_id = tracker.get_slot("contract_id")
        print("contract_id: {0}".format(contract_id))

        last_reading_date = ""
        current_meter_reading = 0
        conn = sqlite3.connect("db/SonnePur.db")
        mycur = conn.cursor()
        sql = """
            SELECT ablesedatum, zaehlerstand FROM verbrauch WHERE vertrag_id = ?;
        """
        mycur.execute(sql, (contract_id,))
        record = mycur.fetchone()
        if record:
            last_reading_date = record[0]
            current_meter_reading = record[1]
        print("date = {0}, meter_reading = {1}".format(last_reading_date, current_meter_reading))
        return [SlotSet("last_reading_date", last_reading_date), SlotSet("current_meter_reading", current_meter_reading)]

class ActionSetMeterReading(Action):
    def name(self) -> Text:
        return "action_set_current_meter_reading"
    # Updates the database with the latest meter reading. The new meter reading is taken
    # from the "meter_reading" slot. It also adds today's date as the new meter reading
    # date.
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        contract_id = tracker.get_slot("contract_id")
        new_meter_reading = tracker.get_slot("meter_reading")
        print("contract_id: {0}, new_meter_reading: {1}".format(contract_id, new_meter_reading))

        date_today = datetime.today().strftime('%Y-%m-%d')

        conn = sqlite3.connect("db/SonnePur.db")
        mycur = conn.cursor()
        sql = """
            UPDATE verbrauch
            SET ablesedatum = ?, zaehlerstand = ?
            WHERE vertrag_id = ?
        """
        mycur.execute(sql, (date_today, new_meter_reading, contract_id,))
        conn.commit()
        return