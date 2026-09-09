from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("risk", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="floodevent",
            old_name="risk_flood_eve_event_d2d0a4_idx",
            new_name="risk_floode_event_d_c94a0d_idx",
        ),
        migrations.RenameIndex(
            model_name="floodevent",
            old_name="risk_flood_eve_distri_9f9d2d_idx",
            new_name="risk_floode_distric_e398c3_idx",
        ),
        migrations.RenameIndex(
            model_name="floodevent",
            old_name="risk_flood_eve_source_4c9d32_idx",
            new_name="risk_floode_source_c802aa_idx",
        ),
        migrations.RenameIndex(
            model_name="hotspotsnapshot",
            old_name="risk_hotsn_snapshot_2d4cb0_idx",
            new_name="risk_hotspo_snapsho_821f4d_idx",
        ),
        migrations.RenameIndex(
            model_name="hotspotsnapshot",
            old_name="risk_hotsn_risk_le_9d47f3_idx",
            new_name="risk_hotspo_risk_le_d297b7_idx",
        ),
        migrations.RenameIndex(
            model_name="riskalert",
            old_name="risk_riska_status__4b83aa_idx",
            new_name="risk_riskal_status_763295_idx",
        ),
        migrations.RenameIndex(
            model_name="riskalert",
            old_name="risk_riska_created_a6f1f1_idx",
            new_name="risk_riskal_created_0321fd_idx",
        ),
        migrations.RenameIndex(
            model_name="riskassessment",
            old_name="risk_riska_observed_1fc8d6_idx",
            new_name="risk_riskas_observe_ead80e_idx",
        ),
        migrations.RenameIndex(
            model_name="riskassessment",
            old_name="risk_riska_risk_le_6ce07d_idx",
            new_name="risk_riskas_risk_le_d8da9f_idx",
        ),
        migrations.RenameIndex(
            model_name="riskzone",
            old_name="risk_riskzon_is_acti_38e1da_idx",
            new_name="risk_riskzo_is_acti_ac6a69_idx",
        ),
        migrations.RemoveField(
            model_name="riskzone",
            name="district",
        ),
        migrations.RemoveField(
            model_name="riskzone",
            name="state",
        ),
        migrations.AlterField(
            model_name="riskalert",
            name="status",
            field=models.CharField(
                choices=[("open", "Open"), ("read", "Read"), ("resolved", "Resolved")],
                default="open",
                max_length=20,
            ),
        ),
    ]
