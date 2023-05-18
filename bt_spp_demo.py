#SPP 示例程序

"""
示例说明:本例程提供一个通过SPP实现与手机端进行数据传输的功能
（1）运行之前,需要先在手机端（安卓）安装蓝牙串口APP,如BlueSPP,然后打开该软件;
（2）修改本例程中的目标设备的蓝牙名称,即 DST_DEVICE_INFO['dev_name'] 的值改为用户准备连接的手机的蓝牙名称;
（3）运行本例程,例程中会先发起搜索周边设备的操作,直到搜索到目标设备,就会结束搜索,然后向目标设备发起SPP连接请求;
（4）用户注意查看手机界面是否弹出蓝牙配对请求的界面,当出现时,点击配对;
（5）配对成功后,用户即可进入到蓝牙串口界面,发送数据给设备,设备在收到数据后会回复"I have received the data you sent."
（6）手机端APP中点击断开连接，即可结束例程;
"""
import bt
import utime
import _thread
from queue import Queue


BT_NAME = 'QuecPython-SPP'

BT_EVENT = {
    'BT_START_STATUS_IND': 0,          # bt/ble start
    'BT_STOP_STATUS_IND': 1,           # bt/ble stop
    'BT_SPP_INQUIRY_IND': 6,           # bt spp inquiry ind
    'BT_SPP_INQUIRY_END_IND': 7,       # bt spp inquiry end ind
    'BT_SPP_RECV_DATA_IND': 14,        # bt spp recv data ind
    'BT_SPP_CONNECT_IND': 61,          # bt spp connect ind
    'BT_SPP_DISCONNECT_IND': 62,       # bt spp disconnect ind
}

DST_DEVICE_INFO = {
    'dev_name':'HUAWEI Mate40 Pro',# 要连接设备的蓝牙名称
    'bt_addr': None
}

BT_IS_RUN = 0
msg_queue = Queue(30)


def bt_callback(args):
    global msg_queue
    msg_queue.put(args)


def bt_event_proc_task():
    global msg_queue
    global BT_IS_RUN
    global DST_DEVICE_INFO

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

                print('Set BT name to {}'.format(BT_NAME))
                retval = bt.setLocalName(0, BT_NAME)
                if retval != -1:
                    print('BT name set successfully.')
                else:
                    print('BT name set failed.')
                    bt.stop()
                    continue

                retval = bt.setVisibleMode(3)
                if retval == 0:
                    mode = bt.getVisibleMode()
                    if mode == 3:
                        print('BT visible mode set successfully.')
                    else:
                        print('BT visible mode set failed.')
                        bt.stop()
                        continue
                else:
                    print('BT visible mode set failed.')
                    bt.stop()
                    continue

                retval = bt.startInquiry(15)
                if retval != 0:
                    print('Inquiry error.')
                    bt.stop()
                    continue
            else:
                print('BT start failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_STOP_STATUS_IND']:
            print('event: BT_STOP_STATUS_IND')
            if status == 0:
                BT_IS_RUN = 0
                print('BT stop successfully.')
            else:
                print('BT stop failed.')

            retval = bt.sppRelease()
            if retval == 0:
                print('SPP release successfully.')
            else:
                print('SPP release failed.')
            retval = bt.release()
            if retval == 0:
                print('BT release successfully.')
            else:
                print('BT release failed.')
            break
        elif event_id == BT_EVENT['BT_SPP_INQUIRY_IND']:
            print('event: BT_SPP_INQUIRY_IND')
            if status == 0:
                rssi = msg[2]
                name = msg[4]
                addr = msg[5]
                mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
                print('name: {}, addr: {}, rssi: {}'.format(name, mac, rssi))

                if name == DST_DEVICE_INFO['dev_name']:
                    print('The target device is found, device name {}'.format(name))
                    DST_DEVICE_INFO['bt_addr'] = addr
                    retval = bt.cancelInquiry()
                    if retval != 0:
                        print('cancel inquiry failed.')
                        continue
            else:
                print('BT inquiry failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_SPP_INQUIRY_END_IND']:
            print('event: BT_SPP_INQUIRY_END_IND')
            if status == 0:
                print('BT inquiry has ended.')
                inquiry_sta = msg[2]
                if inquiry_sta == 0:
                    if DST_DEVICE_INFO['bt_addr'] is not None:
                        print('Ready to connect to the target device : {}'.format(DST_DEVICE_INFO['dev_name']))
                        retval = bt.sppConnect(DST_DEVICE_INFO['bt_addr'])
                        if retval != 0:
                            print('SPP connect failed.')
                            bt.stop()
                            continue
                    else:
                        print('Not found device [{}], continue to inquiry.'.format(DST_DEVICE_INFO['dev_name']))
                        bt.cancelInquiry()
                        bt.startInquiry(15)
            else:
                print('Inquiry end failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_SPP_RECV_DATA_IND']:
            print('event: BT_SPP_RECV_DATA_IND')
            if status == 0:
                datalen = msg[2]
                data = msg[3]
                print('recv {} bytes data: {}'.format(datalen, data))
                send_data = 'I have received the data you sent.'
                print('send data: {}'.format(send_data))
                retval = bt.sppSend(send_data)
                if retval != 0:
                    print('send data faied.')
            else:
                print('Recv data failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_SPP_CONNECT_IND']:
            print('event: BT_SPP_CONNECT_IND')
            if status == 0:
                conn_sta = msg[2]
                addr = msg[3]
                mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
                print('SPP connect successful, conn_sta = {}, addr {}'.format(conn_sta, mac))
            else:
                print('Connect failed.')
                bt.stop()
                continue
        elif event_id == BT_EVENT['BT_SPP_DISCONNECT_IND']:
            print('event: BT_SPP_DISCONNECT_IND')
            conn_sta = msg[2]
            addr = msg[3]
            mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
            print('SPP disconnect successful, conn_sta = {}, addr {}'.format(conn_sta, mac))
            bt.stop()
            continue


def main():
    global BT_IS_RUN

    _thread.start_new_thread(bt_event_proc_task, ())
    retval = bt.init(bt_callback)
    if retval == 0:
        print('BT init successful.')
    else:
        print('BT init failed.')
        return -1
    retval = bt.sppInit()
    if retval == 0:
        print('SPP init successful.')
    else:
        print('SPP init failed.')
        return -1
    retval = bt.start()
    if retval == 0:
        print('BT start successful.')
    else:
        print('BT start failed.')
        retval = bt.sppRelease()
        if retval == 0:
            print('SPP release successful.')
        else:
            print('SPP release failed.')
        return -1

    count = 0
    while True:
        utime.sleep(1)
        count += 1
        cur_time = utime.localtime()
        timestamp = "{:02d}:{:02d}:{:02d}".format(cur_time[3], cur_time[4], cur_time[5])

        if count % 5 == 0:
            if BT_IS_RUN == 1:
                print('[{}] BT SPP is running, count = {}......'.format(timestamp, count))
                print('')
            else:
                print('BT SPP has stopped running, ready to exit.')
                break


if __name__ == '__main__':
    main()