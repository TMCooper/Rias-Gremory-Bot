const Discord = require("discord.js")

module.exports = {

    name: "unban",
    description: "Unban un utilisateur",
    permission: Discord.PermissionFlagsBits.BanMembers,
    dm: false,
    category: "Modération",
    options: [
        {
            type: "user",
            name: "utilisateur",
            description: "Le utilisateur à débannir",
            required: true,
            autocomplete: false
        }, {
            type: "string",
            name: "raison",
            description: "raison du débannissement",
            required: false,
            autocomplete: false
        }
    ],

    async run(bot, message, args) {

        try {

            let user = args.getUser("utilisateur")
            if(!user) return message.reply("Pas de utilisateur à débannir !")

            let reason = args.getString("raison");
            if(!reason) reason = "Pas de raison fournie.";

            if (!(await message.guild.bans.fetch()).get(user.id)) return message.reply("Cette utilisateur n'est pas banni !")

        try {
            await user.send(`Tu as été banni du serveur ${message.user.tag} par ${message.user.tag} pour la raison : \`${reason}\``)
            } catch(err) {}

            await message.reply(`${message.user} a unban ${user.tag} pour la raison : \`${reason}\``)

            await message.guild.members.unban(user, reason)

            } catch (err) {

            return message.reply("pas de utilisateur à débannir ! ") 
        }
    } 
}