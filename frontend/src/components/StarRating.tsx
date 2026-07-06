import { type MouseEvent } from "react";

type StarRatingProps = {
  value: number;
  onChange: (value: number) => void;
};

const MAX_STARS = 5;

export default function StarRating({ value, onChange }: StarRatingProps) {
  const handleClick = (score: number) => (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    onChange(score);
  };

  return (
    <div className="star-rating" role="radiogroup" aria-label="Star rating">
      {Array.from({ length: MAX_STARS }, (_, index) => {
        const score = index + 1;
        const filled = score <= value;
        return (
          <button
            key={score}
            type="button"
            className={filled ? "star-button filled" : "star-button"}
            aria-checked={filled}
            role="radio"
            onClick={handleClick(score)}
          >
            <span className="star">★</span>
          </button>
        );
      })}
    </div>
  );
}
