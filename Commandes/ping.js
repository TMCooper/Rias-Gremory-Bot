const Discord = require("discord.js")

module.exports = { 

    name: "ping",
    description: "Affiche la lattence",
    permission: "Aucune",
    dm: false,
    category: "Informations",

    async run(bot, message, args) {

        await message.reply(`Ping : \`${bot.ws.ping}\``)
    }
}