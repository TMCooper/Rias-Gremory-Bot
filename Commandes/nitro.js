const Discord = require("discord.js")

module.exports = { 

    name: "nitro",
    description: "Genère un code nitro",
    permission: "Aucune",
    dm: false,
    category: "Fun",

    async run(bot, message, args) {
            
            let code = "https://discord.gift/" + Array.from({ length: 16 }, () => Math.random().toString(36).charAt(2)).join('');
            message.reply(`Nitro [GEN] : \`${code}\``)
    }       
}