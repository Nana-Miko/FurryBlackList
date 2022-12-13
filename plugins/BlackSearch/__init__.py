import asyncio

from mplapi.plugin import PyPlugin
from mplapi.mirai import Bot
from mplapi.mirai import msg
from mplapi.plugin import catch_async_exception
from mplapi.plugin import FriendTask
import plugins.BlackSearch.blackApi as api


class KickTask(FriendTask):

    async def execute_task(self, bot: Bot, source: msg.Source, message: msg.MsgChain):
        plain = message.get_plain_msg()
        for i in plain:
            if i.text != '确定踢出':
                bot.send_friend_msg(msg.PlainMsg('操作结束！'), self.target)
                return
        kick_dict: dict = self.plugin_instance.kick_dict
        if kick_dict=={}:
            self.plugin_instance.get_logger().error('Error！无踢出参数')
            return

        group = list(kick_dict.keys())[0]
        target_dict = kick_dict[group]
        for target in target_dict:
            bot.kick(group, target)
            await asyncio.sleep(1)
            bot.send_group_msg(msg.PlainMsg(f'qq {target}已因黑名单被踢出群聊\n原因:{target_dict[target]}'), group)
        bot.send_friend_msg(msg.PlainMsg('踢出完毕！'), self.target)
        self.plugin_instance.kick_dict = {}

    async def on_timeout(self, bot: Bot):
        bot.send_friend_msg(msg.PlainMsg('操作超时！'), self.target)
        self.plugin_instance.kick_dict = {}


class BlackSearchClass(PyPlugin):
    kick_dict = {}

    @property
    def version(self) -> tuple[int, int, int]:
        return 0, 0, 1

    def on_create(self):
        self.get_logger().info('插件启动成功')

    async def on_login(self, bot: Bot):
        bot.register_plugin(self)
        cfg = self.get_config(str(bot.bot_qq))
        if not ('API_KEY' in cfg.keys()):
            cfg['API_KEY'] = ''
            self.set_config(cfg, str(bot.bot_qq))
        perm = bot.get_plugin_permission(self.get_plugin_name())
        perm.set_group_mode(perm.WHITE_LIST_MODE)
        perm.set_friend_mode(perm.WHITE_LIST_MODE)
        bot.set_plugin_permission(self.get_plugin_name(), perm)

    async def on_logout(self, bot: Bot):
        pass

    @catch_async_exception
    async def get_group_msg(self, bot: Bot, source: msg.Source, message: msg.MsgChain):
        pass

    async def get_friend_msg(self, bot: Bot, source: msg.Source, message: msg.MsgChain):
        pass

    @catch_async_exception
    async def get_admin_msg(self, bot: Bot, source: msg.Source, message: msg.MsgChain):
        plain = message.get_plain_msg()
        group = ''
        for i in plain:
            if i.text[:5] == '#群查询 ':
                group = i.text[5:]
        member_dict = {}
        if group != '':
            group = int(group)
            group_member = bot.get_group_member_list(group)
            for member in group_member:
                member_dict[member.id] = member.member_name
        else:
            return

        if len(member_dict) <= 0:
            self.get_logger().error('成员为空或群不存在')
            bot.send_friend_msg(msg.PlainMsg('成员为空或群不存在'), source.sender)
            return

        bot.send_friend_msg(msg.PlainMsg(f'因API每秒25并发限制，因此将会在接下来每秒钟查询5个，大概需要{len(member_dict) / 10}秒'), source.sender)
        note_dict = {}
        count = 0
        for id in member_dict.keys():
            count += 1
            res = blackApi.get_black_list(id, self.get_config(str(bot.bot_qq))['API_KEY'])
            if res[0] == 'true':
                note_dict[id] = res[1]
            if count >= 5:
                await asyncio.sleep(1)
                count = 0

        tips = ''
        for i in note_dict:
            tips += f'{i} {note_dict[i]}\n'

        if len(note_dict) <= 0:
            bot.send_friend_msg(msg.PlainMsg('该群无黑名单'), source.sender)
        else:
            bot.send_friend_msg(msg.PlainMsg(f'黑名单QQ号和群昵称如下:\n{tips}'), source.sender)
            if self.kick_dict=={}:
                self.kick_dict[group] = note_dict
            else:
                self.get_logger().error('错误！存在未完成的task')
                await asyncio.sleep(1)
                bot.send_friend_msg(msg.PlainMsg('请求踢出错误，存在未完成的Task'), source.sender)
            await asyncio.sleep(1)
            bot.send_friend_msg(msg.PlainMsg('请在6秒内输入"确定踢出"来踢出以上群员'), source.sender)
            task = KickTask(source.sender,self)
            task.set_timeout(6)
            bot.add_plugin_task()
