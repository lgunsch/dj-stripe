import decimal

from django.test import TestCase
from djstripe.models import Plan, StaticPlan
from djstripe.admin import PlanAdmin
from django.contrib.admin.sites import AdminSite

from mock import patch


class MockRequest(object):
    pass


class MockForm(object):
    cleaned_data = {}


settings_plans = {
   "plan-id-1": {
        "stripe_plan_id": "test-plan-1",
        "name": "Web App Pro ($24.99/month)",
        "description": "The monthly subscription plan to WebApp",
        "price": 2499,  # $24.99
        "currency": "usd",
        "interval": "month"
    },
   "plan-id-2": {
        "stripe_plan_id": "test-plan-2",
        "name": "Web App ($14.99/month)",
        "description": "The monthly subscription plan to WebApp",
        "price": 1499,  # $24.99
        "currency": "usd",
        "interval": "month"
    },
}

class TestPlan(TestCase):

    def setUp(self):
        self.stripe_id = 'teststripeid'
        self.plan = Plan.objects.create(
            stripe_id=self.stripe_id,
            amount=25000,
            currency='usd',
            interval='week',
            interval_count=1,
            name='A test Stripe Plan',
            trial_period_days=12
        )
        self.site = AdminSite()
        self.plan_admin = PlanAdmin(Plan, self.site)

    @patch("stripe.Plan.retrieve")
    def test_update_name_does_update(self, RetrieveMock):

        self.plan.name = 'a_new_name'
        self.plan.update_name()

        Plan.objects.get(name='a_new_name')

    @patch("stripe.Plan.create")
    @patch("stripe.Plan.retrieve")
    def test_that_admin_save_does_create_new_object(self, RetrieveMock, CreateMock):

        form = MockForm()
        stripe_id = 'admintestid'
        form.cleaned_data = {
            'stripe_id': stripe_id,
            'amount': 25000,
            'currency': 'usd',
            'interval': 'month',
            'interval_count': 1,
            'name': 'A test Admin Stripe Plan',
            'trial_period_days': 12
        }

        self.plan_admin.save_model(request=MockRequest(), obj=None,
                                   form=form, change=False)

        Plan.objects.get(stripe_id=stripe_id)

    @patch("stripe.Plan.create")
    @patch("stripe.Plan.retrieve")
    def test_that_admin_save_does_update_object(self, RetrieveMock, CreateMock):

        self.plan.name = 'A new name'

        self.plan_admin.save_model(request=MockRequest(), obj=self.plan,
                                   form=MockForm(), change=True)

        Plan.objects.get(name=self.plan.name)

    @patch('djstripe.models.DJSTRIPE_PLANS_AS_MODELS', True)
    def test_from_stripe_id_with_model_exists(self):
        plan = Plan.from_stripe_id(self.stripe_id)
        self.assertEqual(plan, self.plan)

    @patch('djstripe.models.DJSTRIPE_PLANS_AS_MODELS', True)
    def test_from_stripe_id_with_model_does_not_exist(self):
        with self.assertRaises(Plan.DoesNotExist):
            Plan.from_stripe_id(settings_plans['plan-id-1']['stripe_plan_id'])

    @patch('djstripe.models.DJSTRIPE_PLANS_AS_MODELS', False)
    @patch('djstripe.models.PAYMENTS_PLANS', settings_plans)
    def test_from_stripe_id_with_settings(self):
        plan = Plan.from_stripe_id(settings_plans['plan-id-1']['stripe_plan_id'])
        expected = StaticPlan('plan-id-1', plan)
        self.assertEqual(plan, expected)

    @patch('djstripe.models.DJSTRIPE_PLANS_AS_MODELS', False)
    def test_from_stripe_id_settings_does_not_exist(self):
        with self.assertRaises(Plan.DoesNotExist):
            Plan.from_stripe_id(self.stripe_id)

class TestStaticPlan(TestCase):

    def test_create_from_settings(self):
        sp = settings_plans['plan-id-1']
        plan = StaticPlan('plan-id-1', sp)
        self.assertEqual(plan.id, 'plan-id-1')
        self.assertEqual(plan.currency, sp['currency'])
        self.assertEqual(plan.name, sp['name'])
        self.assertEqual(plan.interval, sp['interval'])
        self.assertEqual(plan.amount, sp['price'] / decimal.Decimal('100'))

    def test_eq(self):
        sp1 = settings_plans['plan-id-1']
        sp2 = settings_plans['plan-id-2']
        plan1 = StaticPlan('plan-id-1', sp1)
        plan2 = StaticPlan('plan-id-1', sp1)
        plan3 = StaticPlan('plan-id-2', sp2)
        self.assertTrue(plan1 == plan2)
        self.assertTrue(plan1 != plan3)
