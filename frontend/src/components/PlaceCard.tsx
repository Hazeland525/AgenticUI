import React from 'react';
import './PlaceCard.css';

interface PlaceCardProps {
  name: string;
  address?: string;
  rating?: number;
  priceLevel?: string;
  photoUri?: string;
  placeUrl?: string;
}

const PlaceCard: React.FC<PlaceCardProps> = ({
  name,
  address,
  rating,
  priceLevel,
  photoUri,
  placeUrl,
}) => {
  const renderStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const stars = [];

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <span key={`full-${i}`} className="place-card-star">
          ★
        </span>
      );
    }

    if (hasHalfStar && fullStars < 5) {
      stars.push(
        <span key="half" className="place-card-star-half">
          ★
        </span>
      );
    }

    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <span key={`empty-${i}`} className="place-card-star-empty">
          ★
        </span>
      );
    }

    return stars;
  };

  const renderPriceLevel = (level: string) => {
    // priceLevel can be "PRICE_LEVEL_FREE", "PRICE_LEVEL_INEXPENSIVE", 
    // "PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"
    const priceMap: { [key: string]: string } = {
      PRICE_LEVEL_FREE: 'Free',
      PRICE_LEVEL_INEXPENSIVE: '$',
      PRICE_LEVEL_MODERATE: '$$',
      PRICE_LEVEL_EXPENSIVE: '$$$',
      PRICE_LEVEL_VERY_EXPENSIVE: '$$$$',
    };
    return priceMap[level] || '';
  };

  const cardContent = (
    <>
      <div className="place-card-image-container">
        {photoUri ? (
          <img src={photoUri} alt={name} className="place-card-image" />
        ) : (
          <div className="place-card-image-placeholder">No image</div>
        )}
      </div>
      <div className="place-card-content">
        <h3 className="place-card-name">{name}</h3>
        <div className="place-card-meta">
          {rating != null && rating > 0 && (
            <div className="place-card-rating">
              {renderStars(rating)}
              <span className="place-card-rating-value">{rating.toFixed(1)}</span>
            </div>
          )}
          {priceLevel && (
            <span className="place-card-price">{renderPriceLevel(priceLevel)}</span>
          )}
        </div>
        {address && <p className="place-card-address">{address}</p>}
      </div>
    </>
  );

  return placeUrl ? (
    <a
      href={placeUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="place-card"
    >
      {cardContent}
    </a>
  ) : (
    <div className="place-card">{cardContent}</div>
  );
};

export default PlaceCard;
