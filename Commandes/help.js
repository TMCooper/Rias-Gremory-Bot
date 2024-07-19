const Discord = require("discord.js")

module.exports = { 

    name: "help",
    description: "Affiche toutes les commands",
    permission: "Aucune",
    dm: false,
    category: "Informations",
    options: [
        {
            type: "string",
            name: "commande",
            description: "La commande a afficher",
            required: false,
            autocomplete: true
        }
    ],

    async run(bot, message, args) {

        let command;
        if(args.getString("commande")) {
            command = bot.commands.get(args.getString("commande"));
            if(!command) return message.reply("Pas de commande !")
        }

        if(!command) {

            let categories = [];
            bot.commands.forEach(command => {
                if(!categories.includes(command.category)) categories.push(command.category)
            })

            let Embed = new Discord.EmbedBuilder()
            .setColor(bot.color)
            .setTitle(`Commande du bot`)
            .setThumbnail(bot.user.displayAvatarURL({dynamic: true}))
            .setDescription(`Commandes disponibles : \`${bot.commands.size}\` \nCatégories disponibles : \`${categories.lenght}\``)
            .setTimestamp()
            .setFooter({text : "Commandes du bot"})

            await categories.sort().forEach(async cat => {

                let commands = bot.commands.filter(cmd => cmd.category === cat)
                Embed.addFields({name: `${cat}`, value: `${commands.map(cmd => `\`${cmd.name}\` : ${cmd.description}`).join("\n")}` })
            })

            await message.reply({embeds: [Embed]})

        } else{ 

            let Embed = new Discord.EmbedBuilder()
            .setColor(bot.color)
            .setTitle(`Commande ${command.name}`)
            .setThumbnail(bot.user.displayAvatarURL({dynamic: true}))
            .setDescription(`Nom : \`${command.name}\`\nDescription : \`${command.description}\`\nPermission requise \`${command.permission !== "bigint" ? command.permission : new Discord.PermissionsBitsField(command.permission).toArray(false)}\`\nCommande en DM : \`${command.dm ? "Oui" : "Non"}\`\nCategories : \`${command.category}\``)
            .setTimestamp()
            .setFooter({text : "Commandes du bot"})

            await message.reply({embeds: [Embed]})
        }     
    }
}