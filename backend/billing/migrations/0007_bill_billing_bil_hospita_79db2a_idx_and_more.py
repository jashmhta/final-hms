from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0006_remove_bill_bill_status_idx_and_more"),
    ]
    operations = [
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "patient", "status"],
                name="billing_bil_hospita_79db2a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "status", "created_at"],
                name="billing_bil_hospita_409b69_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "appointment"],
                name="billing_bil_hospita_e22fff_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "insurance_claim_status"],
                name="billing_bil_hospita_e90ef0_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(fields=["hospital", "net_cents"], name="billing_bil_hospita_ea5ceb_idx"),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "patient", "created_at"],
                name="billing_bil_hospita_3c611d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(
                fields=["hospital", "status", "net_cents"],
                name="billing_bil_hospita_7cb654_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(fields=["bill"], name="billing_bil_bill_id_2be9b3_idx"),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(fields=["hospital", "department"], name="billing_bil_hospita_2ff083_idx"),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(
                fields=["hospital", "is_outsourced"],
                name="billing_bil_hospita_cf90a8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(
                fields=["hospital", "amount_cents"],
                name="billing_bil_hospita_55e615_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(
                fields=["hospital", "bill", "department"],
                name="billing_bil_hospita_c7493d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="departmentbudget",
            index=models.Index(
                fields=["hospital", "department", "period"],
                name="billing_dep_hospita_1dd298_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="departmentbudget",
            index=models.Index(fields=["hospital", "period"], name="billing_dep_hospita_78ea8a_idx"),
        ),
        migrations.AddIndex(
            model_name="departmentbudget",
            index=models.Index(fields=["hospital", "department"], name="billing_dep_hospita_afea2d_idx"),
        ),
        migrations.AddIndex(
            model_name="departmentbudget",
            index=models.Index(
                fields=["hospital", "budget_cents"],
                name="billing_dep_hospita_f28df0_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["bill"], name="billing_pay_bill_id_6fe91f_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["hospital", "received_at"],
                name="billing_pay_hospita_612c84_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["hospital", "method"], name="billing_pay_hospita_ec19ff_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["hospital", "amount_cents"],
                name="billing_pay_hospita_b2288d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["hospital", "bill", "received_at"],
                name="billing_pay_hospita_d05962_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="servicecatalog",
            index=models.Index(fields=["hospital", "code"], name="billing_ser_hospita_136d3d_idx"),
        ),
        migrations.AddIndex(
            model_name="servicecatalog",
            index=models.Index(fields=["hospital", "active"], name="billing_ser_hospita_d7e46c_idx"),
        ),
        migrations.AddIndex(
            model_name="servicecatalog",
            index=models.Index(
                fields=["hospital", "price_cents"],
                name="billing_ser_hospita_2656f6_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="servicecatalog",
            index=models.Index(
                fields=["hospital", "code", "active"],
                name="billing_ser_hospita_fd4750_idx",
            ),
        ),
    ]
