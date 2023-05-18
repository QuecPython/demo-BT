#A2DP/AVRCP 示例程序

"""
示例说明:本例程提供一个通过A2DP/AVRCP实现的简易蓝牙音乐播放控制功能
运行本例程后,通过手机搜索到设备名并点击连接；然后打开手机上的音乐播放软件,
回到例程运行界面,根据提示菜单输入对应的控制命令来实现音乐的播放,暂停,上一首,
下一首以及设置音量的功能
"""
import bt
import utime
import _thread
from queue import Queue
from machine import Pin

BT_STATUS_DICT = {
    'BT_NOT_RUNNING': 0,
    'BT_IS_RUNNING': 1
}

A2DP_AVRCP_CONNECT_STATUS = {
    'DISCONNECTED': 0,
    'CONNECTING': 1,
    'CONNECTED': 2,
    'DISCONNECTING': 3
}

host_addr = 0
msg_queue = Queue(10)

# 如果对应播放通道外置了PA,且需要引脚控制PA开启,则需要下面步骤
# 具体使用哪个GPIO取决于实际使用的引脚
gpio11 = Pin(Pin.GPIO11, Pin.OUT, Pin.PULL_DISABLE, 0)
gpio11.write(1)


def cmd_proc(cmd):
    cmds = ('1', '2', '3', '4', '5')
    vols = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11')

    if cmd in cmds:
        if cmd == '5':
            while True:
                tmp = input('Please input volume: ')
                if len(tmp) != 1:
                    vol = tmp.split('Please input volume: ')[1]
                else:
                    vol = tmp
                if vol in vols:
                    return cmd, int(vol)
                else:
                    print('Volume should be in [0,11], try again.')
        else:
            return cmd, 0
    else:
        print('Command {} is not supported!'.format(cmd))
        return -1

def avrcp_play(args):
    return bt.avrcpStart()

def avrcp_pause(args):
    return bt.avrcpPause()

def avrcp_prev(args):
    return bt.avrcpPrev()

def avrcp_next(args):
    return bt.avrcpNext()

def avrcp_set_volume(vol):
    return bt.avrcpSetVolume(vol)

def bt_callback(args):
    pass

def bt_a2dp_avrcp_proc_task():
    global msg_queue

    cmd_handler = {
        '1': avrcp_play,
        '2': avrcp_pause,
        '3': avrcp_prev,
        '4': avrcp_next,
        '5': avrcp_set_volume,
    }
    while True:
        # print('wait msg...')
        msg = msg_queue.get()
        print('recv msg: {}'.format(msg))
        cmd_handler.get(msg[0])(msg[1])


def main():
    global host_addr
    global msg_queue

    _thread.start_new_thread(bt_a2dp_avrcp_proc_task, ())
    bt.init(bt_callback)
    bt.setChannel(2)
    retval = bt.a2dpavrcpInit()
    if retval == 0:
        print('BT A2DP/AVRCP initialization succeeded.')
    else:
        print('BT A2DP/AVRCP initialization failed.')
        return -1

    retval = bt.start()
    if retval != 0:
        print('BT start failed.')
        return -1

    utime.sleep_ms(1500)

    old_name = bt.getLocalName()
    if old_name == -1:
        print('Get BT name error.')
        return -1
    print('The current BT name is {}'.format(old_name[1]))
    new_name = 'QuecPython-a2dp'
    print('Set new BT name to {}'.format(new_name))
    retval = bt.setLocalName(0, new_name)
    if retval == -1:
        print('Set BT name failed.')
        return -1
    cur_name = bt.getLocalName()
    if cur_name == -1:
        print('Get new BT name error.')
        return -1
    else:
        if cur_name[1] == new_name:
            print('BT name changed successfully.')
        else:
            print('BT name changed failed.')

    visible_mode = bt.getVisibleMode()
    if visible_mode != -1:
        print('The current BT visible mode is {}'.format(visible_mode))
    else:
        print('Get BT visible mode error.')
        return -1

    print('Set BT visible mode to 3.')
    retval = bt.setVisibleMode(3)
    if retval == -1:
        print('Set BT visible mode error.')
        return -1

    print('BT reconnect check start......')    
    bt.reconnect_set(25, 2)
    bt.reconnect()

    count = 0
    while True:
        count += 1
        if count % 5 == 0:
            print('waiting to be connected...')
        if count >= 10000:
            count = 0
        a2dp_status = bt.a2dpGetConnStatus()
        avrcp_status = bt.avrcpGetConnStatus()
        if a2dp_status == A2DP_AVRCP_CONNECT_STATUS['CONNECTED'] and avrcp_status == A2DP_AVRCP_CONNECT_STATUS['CONNECTED']:
            print('========== BT connected! =========')
            addr = bt.a2dpGetAddr()
            if addr != -1:
                mac = '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(addr[5], addr[4], addr[3], addr[2], addr[1], addr[0])
                print('The BT address on the host side: {}'.format(mac))
                host_addr = addr
            else:
                print('Get BT addr error.')
                return -1
            print('Please open the music player software on your phone first.')
            print('Please enter the following options to select a function:')
            print('========================================================')
            print('1 : play')
            print('2 : pause')
            print('3 : prev')
            print('4 : next')
            print('5 : set volume')
            print('6 : exit')
            print('========================================================')
            while True:
                tmp = input('> ')
                if len(tmp) != 1:
                    cmd = tmp.split('> ')[1]
                else:
                    cmd = tmp
                if cmd == '6':
                    break
                retval = cmd_proc(cmd)
                if retval != -1:
                    msg_queue.put(retval)
            break
        else:
            utime.sleep_ms(1000)
    print('Ready to disconnect a2dp.')
    retval = bt.a2dpDisconnect(host_addr)
    if retval == 0:
        print('a2dp connection disconnected successfully')
    else:
        print('Disconnect a2dp error.')
    print('Ready to stop BT.')
    retval = bt.stop()
    if retval == 0:
        print('BT has stopped.')
    else:
        print('BT stop error.')
    bt.a2dpavrcpRelease()
    bt.release()


if __name__ == '__main__':
    main()