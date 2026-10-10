import React from 'react';
import { ItineraryCard, ItineraryData } from './ItineraryCard';
import { BudgetCard, BudgetCardData } from './BudgetCard';
import { SosCard, SosCardData } from './SosCard';
import { RouteCard, RouteOptionsData } from './RouteCard';
import { WeatherCard, WeatherData } from './WeatherCard';
import { NearMeCard, NearMeData } from './NearMeCard';
import { PhrasebookCard, PhrasebookData } from './PhrasebookCard';
import { PriceTableCard, PriceTableData } from './PriceTableCard';
import { ChecklistCard, ChecklistData } from './ChecklistCard';
import { MultiCityCard, MultiCityData } from './MultiCityCard';

export interface UICardPayload {
  type: string;
  version?: string;
  data: any;
}

interface CardRegistryProps {
  card: UICardPayload;
  onSendChatMessage?: (prompt: string) => void;
  onOpenInspector?: (data: any) => void;
}

export const CardRenderer: React.FC<CardRegistryProps> = ({
  card,
  onSendChatMessage,
  onOpenInspector,
}) => {
  if (!card || !card.type) return null;

  switch (card.type.toLowerCase()) {
    case 'itinerary':
      return (
        <ItineraryCard
          data={card.data as ItineraryData}
          onSendChatMessage={onSendChatMessage}
          onOpenInspector={onOpenInspector}
        />
      );

    case 'budget':
      return (
        <BudgetCard
          data={card.data as BudgetCardData}
          onSendChatMessage={onSendChatMessage}
        />
      );

    case 'sos':
    case 'safety':
    case 'medical':
      return (
        <SosCard
          data={card.data as SosCardData}
          onSendChatMessage={onSendChatMessage}
        />
      );

    case 'route_options':
    case 'transport':
      return (
        <RouteCard
          data={card.data as RouteOptionsData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'weather':
      return (
        <WeatherCard
          data={card.data as WeatherData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'near_me':
    case 'places_near_me':
      return (
        <NearMeCard
          data={card.data as NearMeData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'phrasebook':
      return (
        <PhrasebookCard
          data={card.data as PhrasebookData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'price_table':
    case 'fair_price':
    case 'entry_fees':
      return (
        <PriceTableCard
          data={card.data as PriceTableData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'checklist':
    case 'packing_list':
      return (
        <ChecklistCard
          data={card.data as ChecklistData}
          onSendMessage={onSendChatMessage}
        />
      );

    case 'multi_city':
    case 'optimizer':
      return (
        <MultiCityCard
          data={card.data as MultiCityData}
          onSendMessage={onSendChatMessage}
        />
      );

    default:
      return null;
  }
};

