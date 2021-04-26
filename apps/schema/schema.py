from graphene_django import DjangoObjectType
import graphene
from django.utils import timezone
from apps.users.models import User 
from apps.decks.models import Deck as DeckModel
from apps.cards.models import Card as CardModel

from apps.decks.schema import (
    DeckType,
    CreateDeck
)

buckets = (
        (1, 1),
        (2, 3),
        (3, 7),
        (4, 16),
        (5, 30),
    )

def return_date_time(days):
  now = timezone.now()
  return now + timezone.timedelta(days=days)

class UserType(DjangoObjectType):
    class Meta:
        model = User

class Deck(DjangoObjectType):
  class Meta:
        model = DeckModel

class Card(DjangoObjectType):
  class Meta:
        model = CardModel

class UpdateCard(graphene.Mutation):
  card = graphene.Field(Card)

  class Arguments:
    id = graphene.ID()
    question = graphene.String()
    answer = graphene.String()
    # easy, average, dificult. Moving buckets/date in future when they are reviewed
    status = graphene.Int()

  def mutate(self, info, id, question, answer, status):
    c = CardModel.objects.get(id=id)
    bucket = c.bucket

    if status == 1 and bucket > 1:
      bucket -= 1
    elif status == 3 and bucket <= 4:
      bucket += 1

    # Calc next review at date
    days = buckets[bucket-1][1]
    next_review_at = return_date_time(days)

    
    c.question = question
    c.answer = answer
    c.bucket = bucket
    c.next_review_at = next_review_at
    c.last_reviewed_at = timezone.now()
    c.save()
    
    return UpdateCard(card=c)

class CreateDeck(graphene.Mutation):
    deck = graphene.Field(Deck)

    class Arguments:
        title = graphene.String()
        description = graphene.String()

    def mutate(self, info, title , description):
        d = DeckModel(title=title, description=description)
        d.save()
        return CreateDeck(deck=d)

class CreateCard(graphene.Mutation):
    card = graphene.Field(Card)

    class Arguments:
        question = graphene.String()
        answer = graphene.String()
        deck_id = graphene.Int()

    def mutate(self, info, question, answer, deck_id):
        c = CardModel(question=question, answer=answer)
        d = DeckModel.objects.get(id=deck_id)
        c.deck = d
        c.save()
        return CreateCard(card=c)

class Mutation(graphene.ObjectType):
    create_card = CreateCard.Field()
    create_deck = CreateDeck.Field()
    update_card = UpdateCard.Field()

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    decks = graphene.List(DeckType)
    deck_by_id = graphene.Field(DeckType, id=graphene.Int())
    cards = graphene.List(Card)
    deck_cards = graphene.List(Card, deck = graphene.Int())

    def resolve_users(self, info):
        return User.objects.all()
    
    def resolve_decks(self, info):
      return DeckModel.objects.all()

    def resolve_deck_cards(self, info, deck):
      return CardModel.objects.filter(deck=deck)

    def resolve_decks_by_id(self, info, id):
      return DeckModel.objects.get(id=id)
    
    def resolve_cards(seld, info):
      return CardModel.objects.all()



schema = graphene.Schema(query=Query, mutation=Mutation)