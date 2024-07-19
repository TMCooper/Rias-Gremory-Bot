const Discord = require("discord.js")

module.exports = async (bot, interaction) => {

    if(interaction.type === Discord.InteractionType.ApplicationCommandAutocomplete) {

        let entry = interaction.options.getFocused()
        
        if(interaction.commandName === "help") {

            let choices = bot.commands.filter(cmd => cmd.name.includes(entry))
            await interaction.respond(entry === "" ? bot.commands.map(cmd => ({name: cmd.name, value: cmd.name})) : choices.map(choice => ({name: choice.name, value: choice.name})))
        }

        if(interaction.commandName === "setcaptcha" || interaction.commandName === "setantiraid" || interaction.commandName === "setantispam") {

            let choices = ["on", "off"]
            let sortie = choices.filter(c => c.includes(entry))
            await interaction.respond(entry === "" ? sortie.map(c => ({name: c, value: c})) : sortie.map(c => ({name: c, value: c})))
        }

        if(interaction.commandName === "roles") {

            let choices = ["add", "remove"]
            let sortie = choices.filter(c => c.includes(entry))
            await interaction.respond(entry === "" ? sortie.map(c => ({name: c, value: c})) : sortie.map(c => ({name: c, value: c})))
        }

        if(interaction.commandName === "setstatus") {

            let choices = ["Listening", "Watching", "Playing", "Streaming", "Competing"]
            let sortie = choices.filter(c => c.includes(entry))
            await interaction.respond(entry === "" ? sortie.map(c => ({name: c, value: c})) : sortie.map(c => ({name: c, value: c})))
        }
    }

    if(interaction.type === Discord.InteractionType.ApplicationCommand) {

        let command = require(`../Commandes/${interaction.commandName}`)
        command.run(bot, interaction, interaction.options, bot.db)
    }

    if(interaction.isButton()) {

        if(interaction.customId === "ticket") {

            let channel = await interaction.guild.channels.create({
                name: `ticket-${interaction.user.username}`,
                type: Discord.ChannelType.GuildText,
            })
            await channel.setParent(interaction.channel.parent.id)

            await channel.permissionOverwrites.create(interaction.guild.roles.everyone, {
                ViewChannel: false
            })
            await channel.permissionOverwrites.create(interaction.user, {
                ViewChannel: true,
                EmbedLinks: true,
                SendMessages: true,
                AttachFiles: true,
                ReadMessageHistory: true,
            })
            await channel.permissionOverwrites.create("1079530798186778704", {
                ViewChannel: true,
                EmbedLinks: true,
                SendMessages: true,
                AttachFiles: true,
                ReadMessageHistory: true,
            })

            await channel.setTopic(interaction.user.id)
            await interaction.reply({content: `Votre ticket a correctement été créé : ${channel}`, ephemeral: true})

            let Embed = new Discord.EmbedBuilder()
            .setColor(bot.color)
            .setTitle("Création d'un ticket")
            .setThumbnail(bot.user.displayAvatarURL({dynamic: true}))
            .setDescription("Ticket créé")
            .setTimestamp()
            .setFooter({text: bot.user.username, iconURL: bot.user.displayAvatarURL({dynamic: true})})

            const btn = new Discord.ActionRowBuilder().addComponents(new Discord.ButtonBuilder()
            .setCustomId("close")
            .setLabel("Ferme un ticket")
            .setStyle(Discord.ButtonStyle.Primary)
            .setEmoji("🚮"))

            await channel.send({embeds: [Embed], components: [btn]})
        }

        if(interaction.customId === "close") {

            let user = bot.users.cache.get(interaction.channel.topic)
            try {await user.send("Votre tiket a été fermé")} catch (err) {}

            await interaction.channel.delete()
        }
    }

    if(interaction.isStringSelectMenu()) {

        if(interaction.customId === "reactionrole") {

            bot.db.query(`SELECT * FROM server WHERE guild = '${interaction.guildId}'`, async (err, req) =>{

                let roles = req[0].reactionrole.split(" ");
                if(roles.length <= 0) return;

                //await interaction.deferReply({ephemeral: true})
                
                let retireroles = [];
                let addroles = [];
                for(let i = 0; i < roles.length; i++) {
                    if(interaction.member.roles.cache.has(roles[i]) && !interaction.values.includes(roles[i])) {
                        interaction.member.roles.remove(roles[i])
                        retireroles.push(roles[i])
                    }
                }
                for(let i = 0; i < interaction.values.length; i++) {
                    interaction.member.roles.add(interaction.values[i])
                    addroles.push(interaction.values[i])
                }

                interaction.reply({content: "Les rôles ont été modifiés", ephemeral: true})

                //await interaction.followUp({content: `${addroles.length <= 0 ? "" :`Les rôles ${addroles.map(r => `\`${interaction.guild.roles.cache.get(r).name}\``).join(", ")} Vous on été ajoutés.`} ${retireroles.length <= 0 ? "" : `Les rôles \`${retireroles.map(r => `\`${interaction.guild.roles.cache.get(r).name}\``).join(", ")} vous ont été retirés.`}`, ephemeral: true})
            })
        }
    }
}