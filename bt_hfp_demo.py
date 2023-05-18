#HFP 示例程序

"""
示例说明:本例程提供一个通过HFP自动接听电话的功能
运行平台:EC600UCN_LB 铀开发板
运行本例程后,通过手机A搜索到设备名并点击连接;然后通过手机B拨打电话给手机A,
当手机A开始响铃震动时,设备会自动接听电话
"""
import bt
import utime
import _thread
from queue import Queue
from machine import Pin

# 如果对应播放通道外置了PA,且需要引脚控制PA开启,则需要下面步骤
# 具体使用哪个GPIO取决于实际使用的引脚
gpio11 = Pin(Pin.GPIO11, Pin.OUT, Pin.PULL_DISABLE, 0)
gpio11.write(1)

BT_NAME = 'QuecPython-hfp'

BT_EVENT = {
    'BT_START_STATUS_IND': 0,           # bt/ble start
    'BT_STOP_STATUS_IND': 1,            # bt/ble stop
    'BT_HFP_CONNECT_IND': 40,           # bt hfp connected
    'BT_HFP_DISCONNECT_IND': 41,        # bt hfp disconnected
    'BT_HFP_CALL_IND': 42,              # bt hfp call state
    'BT_HFP_CALL_SETUP_IND': 43,        # bt hfp call setup state
    'BT_HFP_NETWORK_IND': 44,           # bt hfp network state
    'BT_HFP_NETWORK_SIGNAL_IND': 45,    # bt hfp network signal
    'BT_HFP_BATTERY_IND': 46,           # bt hfp battery level
    'BT_HFP_CALLHELD_IND': 47,          # bt hfp callheld state
    'BT_HFP_AUDIO_IND': 48,             # bt hfp audio state
    'BT_HFP_VOLUME_IND': 49,            # bt hfp volume type
    'BT_HFP_NETWORK_TYPE': 50,          # bt hfp network type
    'BT_HFP_RING_IND': 51,              # bt hfp ring indication
    'BT_HFP_CODEC_IND': 52,             # bt hfp codec type
}

HFP_CONN_STATUS = 0
HFP_CONN_STATUS_DICT = {
    'HFP_DISCONNECTED': 0,
    'HFP_CONNECTING': 1,
    'HFP_CONNECTED': 2,
    'HFP_DISCONNECTING': 3,
}
HFP_CALL_STATUS = 0
HFP_CALL_STATUS_DICT = {
    'HFP_NO_CALL_IN_PROGRESS': 0,
    'HFP_CALL_IN_PROGRESS': 1,
}

BT_IS_RUN = 0

msg_queue = Queue(30)


def get_key_by_value(val, d):
    for key, value in d.items():
        if val == value:
            return key
    return None

def bt_callback(args):
    global msg_queue
    msg_queue.put(args)

def bt_event_proc_task():
    global msg_queue
    global BT_IS_RUN
    global BT_EVENT
    global HFP_CONN_STATUS
    global HFP_CONN_STATUS_DICT
    global HFP_CALL_STATUS
    global HFP_CALL_STATUS_DICT

    while True:
        print('wait msg...')
        msg = msg_queue.get()  # 没有消息时会阻塞在这
        event_id = msg[0]
        status = msg[1]

        if event_id == BT_EVENT['BT_START_STATUS_IND']:
            print('event: BT_START_STATUS_IND')
            if status == 0:
                print('BT start successfully.')
                BT_IS_RUN = 1
                bt_status = bt.getStatus()
                if bt_status == 1:
                    print('BT status is 1, normal status.')
                else:
                    print('BT status is {}, abnormal status.'.format(bt_status))
                    bt.stop()
                    break

                retval = bt.getLocalName()
                if retval != -1:
                    print('The current BT name is : {}'.format(retval[1]))
                else:
                    print('Failed to get BT name.')
                    bt.stop()
                    break

                print('Set BT name to {}'.format(BT_NAME))
                retval = bt.setLocalName(0, BT_NAME)
                if retval != -1:
                    print('BT name set successfully.')
                else:
                    print('BT name set failed.')
                    bt.stop()
                    break

                retval = bt.getLocalName()
                if retval != -1:
                    print('The new BT name is : {}'.format(retval[1]))
                else:
                    print('Failed to get new BT name.')
                    bt.stop()
                    break

                # 设置蓝牙可见模式为:可以被发现并且可以被连接
                retval = bt.setVisibleMode(3)
                if retval == 0:
                    mode = bt.getVisibleMode()
                    if mode == 3:
                        print('BT visible mode set successfully.')
                    else:
                        print('BT visible mode set failed.')
                        bt.stop()
                        break
                else:
                    print('BT visible mode set failed.')
                    bt.stop()
                    break
            else:
                print('BT start failed.')
                bt.stop()
                break
        elif event_id == BT_EVENT['BT_STOP_STATUS_IND']:
            print('event: BT_STOP_STATUS_IND')
            if status == 0:
                BT_IS_RUN = 0
                print('BT stop successfully.')
            else:
                print('BT stop failed.')
            break
        elif event_id == BT_EVENT['BT_HFP_CONNECT_IND']:
            HFP_CONN_STATUS = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_CONNECT_IND, {}, hfp_conn_status:{}, mac:{}'.format(status, get_key_by_value(msg[2], HFP_CONN_STATUS_DICT), mac))
            if status != 0:
                print('BT HFP connect failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_DISCONNECT_IND']:
            HFP_CONN_STATUS = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_DISCONNECT_IND, {}, hfp_conn_status:{}, mac:{}'.format(status, get_key_by_value(msg[2], HFP_CONN_STATUS_DICT), mac))
            if status != 0:
                print('BT HFP disconnect failed.')
            bt.stop()
        elif event_id == BT_EVENT['BT_HFP_CALL_IND']:
            call_sta = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_CALL_IND, {}, hfp_call_status:{}, mac:{}'.format(status, get_key_by_value(msg[2], HFP_CALL_STATUS_DICT), mac))
            if status != 0:
                print('BT HFP call failed.')
                bt.stop()
                continue

            if call_sta == HFP_CALL_STATUS_DICT['HFP_NO_CALL_IN_PROGRESS']:
                if HFP_CALL_STATUS == HFP_CALL_STATUS_DICT['HFP_CALL_IN_PROGRESS']:
                    HFP_CALL_STATUS = call_sta
                    if HFP_CONN_STATUS == HFP_CONN_STATUS_DICT['HFP_CONNECTED']:
                        print('call ended, ready to disconnect hfp.')
                        retval = bt.hfpDisconnect(addr)
                        if retval == 0:
                            HFP_CONN_STATUS = HFP_CONN_STATUS_DICT['HFP_DISCONNECTING']
                        else:
                            print('Failed to disconnect hfp connection.')
                            bt.stop()
                            continue
            else:
                if HFP_CALL_STATUS == HFP_CALL_STATUS_DICT['HFP_NO_CALL_IN_PROGRESS']:
                    HFP_CALL_STATUS = call_sta
                    print('set audio output channel to 2.')
                    bt.setChannel(2)
                    print('set volume to 7.')
                    retval = bt.hfpSetVolume(addr, 7)
                    if retval != 0:
                        print('set volume failed.')
        elif event_id == BT_EVENT['BT_HFP_CALL_SETUP_IND']:
            call_setup_status = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_CALL_SETUP_IND, {}, hfp_call_setup_status:{}, mac:{}'.format(status, call_setup_status, mac))
            if status != 0:
                print('BT HFP call setup failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_CALLHELD_IND']:
            callheld_status = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_CALLHELD_IND, {}, callheld_status:{}, mac:{}'.format(status, callheld_status, mac))
            if status != 0:
                print('BT HFP callheld failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_NETWORK_IND']:
            network_status = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_NETWORK_IND, {}, network_status:{}, mac:{}'.format(status, network_status, mac))
            if status != 0:
                print('BT HFP network status failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_NETWORK_SIGNAL_IND']:
            network_signal = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_NETWORK_SIGNAL_IND, {}, signal:{}, mac:{}'.format(status, network_signal, mac))
            if status != 0:
                print('BT HFP network signal failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_BATTERY_IND']:
            battery_level = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_BATTERY_IND, {}, battery_level:{}, mac:{}'.format(status, battery_level, mac))
            if status != 0:
                print('BT HFP battery level failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_AUDIO_IND']:
            audio_status = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_AUDIO_IND, {}, audio_status:{}, mac:{}'.format(status, audio_status, mac))
            if status != 0:
                print('BT HFP audio failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_VOLUME_IND']:
            volume_type = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_VOLUME_IND, {}, volume_type:{}, mac:{}'.format(status, volume_type, mac))
            if status != 0:
                print('BT HFP volume failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_NETWORK_TYPE']:
            service_type = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_NETWORK_TYPE, {}, service_type:{}, mac:{}'.format(status, service_type, mac))
            if status != 0:
                print('BT HFP network service type failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_RING_IND']:
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_RING_IND, {}, mac:{}'.format(status, mac))
            if status != 0:
                print('BT HFP ring failed.')
                bt.stop()
                continue
            retval = bt.hfpAnswerCall(addr)
            if retval == 0:
                print('The call was answered successfully.')
            else:
                print('Failed to answer the call.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_HFP_CODEC_IND']:
            codec_type = msg[2]
            addr = msg[3]  # BT 主机端mac地址
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('BT_HFP_CODEC_IND, {}, codec_type:{}, mac:{}'.format(status, codec_type, mac))
            if status != 0:
                print('BT HFP codec failed.')
                bt.stop()
                continue
    print('Ready to release hfp.')
    bt.hfpRelease()
    bt.release()


def main():
    global BT_IS_RUN

    _thread.start_new_thread(bt_event_proc_task, ())

    retval = bt.init(bt_callback)
    if retval == 0:
        print('BT init successful.')
    else:
        print('BT init failed.')
        return -1
    retval = bt.hfpInit()
    if retval == 0:
        print('HFP init successful.')
    else:
        print('HFP init failed.')
        return -1
    retval = bt.start()
    if retval == 0:
        print('BT start successful.')
    else:
        print('BT start failed.')
        retval = bt.hfpRelease()
        if retval == 0:
            print('HFP release successful.')
        else:
            print('HFP release failed.')
        retval = bt.release()
        if retval == 0:
            print('BT release successful.')
        else:
            print('BT release failed.')
        return -1

    count = 0
    while True:
        utime.sleep(1)
        count += 1
        cur_time = utime.localtime()
        timestamp = "{:02d}:{:02d}:{:02d}".format(cur_time[3], cur_time[4], cur_time[5])

        if count % 5 == 0:
            if BT_IS_RUN == 1:
                print('[{}] BT HFP is running, count = {}......'.format(timestamp, count))
                print('')
            else:
                print('BT HFP has stopped running, ready to exit.')
                break


if __name__ == '__main__':
    main()
