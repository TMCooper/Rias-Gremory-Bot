const Discord = require('discord.js')

module.exports = {

    name: "setantispam",
    description: "Paramètre l'antispam",
    permission: Discord.PermissionFlagsBits.ManageGuild,
    dm: false,
    category: "Administration",
    options: [
        {
            type: "string",
            name: "état",
            description: "Etat de l'antispam (on ou off)",
            required: true,
            autocomplete: true
        }
    ],

    async run(bot, message, args, db) {
        
        let etat = args.getString("état")
        if(etat !== "on" && etat !== "off") return message.reply("Indique on ou off")

        if(etat === "off") {

            db.query(`UPDATE server SET antispam = 'false' WHERE guild = '${message.guildId}'`)
            await message.reply("L'antispam est bien desactivé !")

        } else {

            db.query(`UPDATE server SET antispam = 'true' WHERE guild = '${message.guildId}'`)
            await message.reply(`L'antispam est bien activé !`)
        }
    }
}