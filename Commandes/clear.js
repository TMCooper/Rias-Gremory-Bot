const Discord = require("discord.js")
const ms = require("ms")

module.exports = {

    name: "clear",
    description: "Efface beaucoup de messages",
    permission: Discord.PermissionFlagsBits.ManageMessages,
    dm: false,
    category: "Modération",
    options: [
        {
            type: "number",
            name: "nombre",
            description: "Le nombre de messages à supprimer",
            required: true,
            autocomplete: false
        }, {
            type: "channel",
            name: "salon",
            description: "Le salon où effacer les messages",
            required: false,
            autocomplete: false
        }
    ],

    async run(bot, message, args) {

        let channel = args.getChannel("salon")
        if(!channel) channel = message.channel;
        if(channel.id !== message.channel.id && !message.guild.channels.cache.get(channel.id)) return message.reply("Pas de salon trouvé !")

        let number = args.getNumber("nombre")
        if(parseInt(number) <= 0 || parseInt(number) > 100) return message.reply("Il faut un nombre entre `0`et `100` inclus !")

        
        await message.reply({ content: "Rias réflechie", ephemeral: true });

        try {

            let messages = await channel.bulkDelete(parseInt(number))

            await message.editReply({content: `J'ai supprimé \`${messages.size}\` messages dans le salon \`${channel.name}\``,ephemeral: true});

        } catch (err) {
            
            let messages = [...(await channel.messages.fetch()).filter(msg => !msg.interaction && (Date.now() - msg.createdAt) <= 1209600000).values()]
            if (messages.length <= 0) return message.followUp("Aucun message à supprimer car ils datent tous de plus de 14 jours !");
            await channel.bulkDelete(messages)

            await message.editReply({
                content: `J'ai pu supprimer uniquement \`${messages.length}\` messages dans le salon \`${channel.name}\` car les autres datent de plus de 14 jours !`,                ephemeral: true
              });
        }

    }
}