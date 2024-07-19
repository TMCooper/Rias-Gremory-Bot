const Discord = require("discord.js")

module.exports = {

    name: "kick",
    description: "Kick un membre",
    permission: Discord.PermissionFlagsBits.KickMembers,
    dm: false,
    category: "Modération",
    options: [
        {
            type: "user",
            name: "membre",
            description: "Le membre a kick",
            required: true,
            autocomplete: false
        }, {
            type: "string",
            name: "raison",
            description: "La raison du kick",
            required: false,
            autocomplete: false
        }
    ],

    async run(bot, message, args) {

        
        let user = args.getUser("membre")
        if(!user) return message.reply("Pas de membre a kick !")
        let member = message.guild.members.cache.get(user.id)
        if(!member) return message.reply("Pas de membre a kick !")

        let reason = args.getString("raison")
        if(!reason) reason = "Pas de raison fournie.";

        if(message.user.id === user.id) return message.reply("N'essaie pas de te kick !")
        if((await message.guild.fetchOwner()).id === user.id) return message.reply("Ne kick pas le proprietaire du serveur !")
        if(member && !member.kickable) return message.reply("Je ne peut pas kick se membre !")
        if(member && message.member.roles.highest.comparePositionTo(member.roles.highest) <= 0) return message.reply("Tu ne peut pas kick cette personne !")

        try {await user.send(`Tu a été kick du serveur ${message.guild.name} par ${message.user.tag} pour la raison : \`${reason}\``)} catch(err) {}

        await message.reply(`${message.user} a kick ${user.tag} pour la raison : \`${reason}\``)
            
        await member.kick(reason)
    }
}