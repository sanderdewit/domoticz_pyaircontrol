# Domoticz plugin to interact with Philips air purifiers
#
# Author: Bruno Obsomer
#
"""
<plugin key="pyaircontrol" name="Philips air purifier plugin" author="Bruno Obsomer" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/bobzomer/domoticz_pyaircontrol">
    <description>
        <h2>Philips air purifier plugin</h2><br/>
        Domoticz plugin to interact with Philips air purifiers
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Feature one...</li>
            <li>Feature two...</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Device Type - What it does...</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
        <param field="Address" label="Philips air purifier address" width="300px" required="true"/>
        <param field="Mode1" label="Protocol" width="300px" required="true">
            <options>
                <option label="HTTP" value="http"/>
                <option label="CoAP" value="coap"/>
                <option label="¨Plain CoAP" value="plain_coap"/>
            </options>
        </param>
    </params>
</plugin>
"""
import threading

import Domoticz
import pyairctrl.coap_client
import pyairctrl.airctrl


class PyAirControl:
    POLLING_DELAY = 10.0  # s
    enabled = False

    devices = [
        ("pwr", "Power", 244, 62, {"Switchtype": 0}),
        ("pm25", "PM2.5", 243, 31, {"Custom": "1;µg/m³"}),
        ("rh", "Relative humidity", 81, 1, {}),
        ("rhset", "Target humidity", 81, 1, {}),
        ("iaql", "Allergen index", 249, 1, {}),
        ("temp", "Temperature", 80, 5, {}),
        ("mode", "Mode", 0, 0, {}),
        ("om", "Fan speed", 0, 0, {}),
        ("aqil", "Light brightness", 0, 0, {}),
        ("aqit", "Air quality notification threshold", 0, 0, {}),
        ("uil", "Buttons light", 244, 62, {"Switchtype": 0}),
        ("ddp", "Used index", 0, 0, {}),
        ("wl", "Water level", 0, 0, {}),
        ("cl", "Child lock", 0, 0, {}),
        ("dt", "Timer", 0, 0, {}),
        ("dtrs", "Timer", 0, 0, {}),
        ("fltt1", "HEPA filter type", 0, 0, {}),
        ("fltt2", "Active carbon filter type", 0, 0, {}),
        ("fltsts0", "Pre-filter and Wick", 243, 31, {"Custom": "1;Hours"}),
        ("fltsts1", "HEPA filter", 243, 31, {"Custom": "1;Hours"}),
        ("fltsts2", "Active carbon filter", 243, 31, {"Custom": "1;Hours"}),
        ("wicksts", "Wick filter", 243, 31, {"Custom": "1;Hours"}),
        ("err", "[ERROR] Message", 243, 22, {}),
    ]

    def __init__(self):
        self.protocol = None
        self.device_address = None
        self.client: pyairctrl.coap_client.HTTPAirClientBase

    def checkDevices(self):
        for index, (_, name, type_, subtype, options) in enumerate(self.devices):
            if index + 1 not in Devices and type_ != 0:
                Domoticz.Log("Create " + name)
                Domoticz.Device(Name=name, Unit=index + 1, Type=type_, Subtype=subtype, Options=options).Create()

    def onPollDevice(self):
        status = self.client.get_status()
        for index, (_, name, type_, subtype, options) in enumerate(self.devices):
            if type_ == 0:  # Not yet enabled
                continue
            try:
                value = status[name]
                if type_ == 244:
                    Devices[index + 1].Update(nValue=value, sValue={'1': 'on', '0': 'off'}.get(value, 'off'))
                else:
                    Devices[index + 1].Update(nValue=1, sValue=str(value))
            except KeyError:
                pass

    def onStart(self):
        self.protocol = Parameters["Mode1"]
        self.device_address = Parameters["Address"].replace(" ", "")
        self.checkDevices()

        if self.protocol == 'http':
            c = pyairctrl.airctrl.HTTPAirClient(self.device_address)
            c.load_key()
        elif self.protocol == 'plain_coap':
            c = pyairctrl.airctrl.PlainCoAPAirClient(self.device_address)
        elif self.protocol == 'coap':
            c = pyairctrl.airctrl.CoAPAirClient(self.device_address)
        else:
            raise NotImplementedError(f"Unknown protocol {self.protocol}")
        self.client = c

        Domoticz.Log("onStart called")

    def onStop(self):
        Domoticz.Log("onStop called")
        self.poll_thread_stop.set()
        self.poll_thread.join()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        self.client.set_values({Command: Level})

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        self.onPollDevice()


global _plugin
_plugin = PyAirControl()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
