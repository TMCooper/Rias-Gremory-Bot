const Discord = require("discord.js")
const User = new Map()

module.exports = async message => {

    if(message.member.permissions.has(Discord.PermissionFlagsBits.ManageMessages)) return;

    if(User.get(message.author.id)) {

        const data = User.get(message.author.id)
        let difference = message.createdTimestamp - data.lastMessage.createdTimestamp;
        let count = data.msgCount;

        if(difference > 3000) {

            clearTimeout(data.timer)
            data.msgCount = 1;
            data.lastMessage = message;

            data.timer = setTimeout(() => {
                User.delete(message.author.id)
            }, 5000)

            User.set(message.author.id, data)

        } else {

            count++;

            if(count > 5) {

                await message.channel.send(`Attention ${message.author} est maudie !`)
                await message.member.timeout(300000, "Spam")

                const messages = [...(await message.channel.messages.fetch({before: message.id})).filter(m => m.author.id === message.author.id).values()].slice(0, 10)
                await message.channel.bulkDelete(messages)

            } else {

                data.msgCount = count;
                User.set(message.author.id, data)
            }
        }

    } else {

        let FN = setTimeout(() => {
            User.delete(message.author.id)
        }, 600000)

        User.set(message.author.id, {
            msgCount: 1,
            lastMessage: message,
            timer: FN
        })
    }
}