import React from "react";
import type { Shop, ShopItem } from "../types/gameplay";

interface ShopOverlayProps {
  shop: Shop;
  characterGold: number;
  busy: boolean;
  onPurchase: (item: ShopItem) => void;
  onClose: () => void;
  lastPurchase?: string | null;
  error?: string | null;
}

const ShopOverlay: React.FC<ShopOverlayProps> = ({
  shop,
  characterGold,
  busy,
  onPurchase,
  onClose,
  lastPurchase,
  error,
}) => {
  return (
    <div className="shop-overlay-backdrop" onClick={onClose}>
      <section
        className="kenney-panel shop-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2>{shop.name}</h2>
          <button
            type="button"
            className="kenney-button secondary"
            onClick={onClose}
            disabled={busy}
          >
            Close
          </button>
        </div>
        <p className="shop-description">{shop.description}</p>

        {lastPurchase && (
          <div className="success-banner" role="status">
            ✓ Purchased {lastPurchase}!
          </div>
        )}

        {error && (
          <div className="error-banner" role="alert">
            ⚠ {error}
          </div>
        )}

        <div className="gold-display">
          <span className="eyebrow">Your Gold:</span> 💰 {characterGold}g
        </div>

        <div className="shop-inventory">
          {shop.items.map((item) => (
            <article key={item.item_id} className="grid-card shop-item-card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                }}
              >
                <h4 style={{ margin: 0 }}>{item.name}</h4>
                <span className="price-tag">💰 {item.price}g</span>
              </div>
              <p className="item-description">{item.description}</p>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginTop: "0.5rem",
                }}
              >
                <span className={`rarity-tag ${item.rarity.toLowerCase()}`}>
                  {item.rarity}
                </span>
                <button
                  type="button"
                  className={
                    characterGold < item.price
                      ? "kenney-button disabled"
                      : "kenney-button"
                  }
                  disabled={busy || characterGold < item.price}
                  onClick={() => onPurchase(item)}
                >
                  {characterGold < item.price ? "Insufficient Gold" : "Buy"}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <style>{`
        .shop-overlay-backdrop {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 2rem;
        }
        .shop-modal {
          max-width: 600px;
          width: 90%;
          max-height: 85vh;
          overflow-y: auto;
          background: #2c3e50;
          color: white;
          box-shadow: 0 0 20px rgba(0,0,0,0.5);
          position: relative;
        }
        .shop-description {
          font-style: italic;
          color: #94a3b8;
          margin-bottom: 1.5rem;
        }
        .item-description {
          font-size: 0.85rem;
          margin: 0.5rem 0;
          color: #cbd5e1;
        }
        .success-banner {
          background: rgba(34, 197, 94, 0.2);
          color: #86efac;
          padding: 0.5rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          text-align: center;
          border: 1px solid #22c55e;
        }
        .error-banner {
          background: rgba(239, 68, 68, 0.2);
          color: #fca5a5;
          padding: 0.5rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          text-align: center;
          border: 1px solid #ef4444;
        }
        .gold-display {
          background: rgba(0,0,0,0.3);
          padding: 0.5rem 1rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          font-weight: bold;
          color: #fef08a;
        }
        .shop-inventory {
          display: grid;
          gap: 1rem;
        }
        .shop-item-card {
          border: 1px solid rgba(255,255,255,0.1);
        }
        .price-tag {
          color: #fef08a;
          font-weight: bold;
        }
        .rarity-tag {
          font-size: 0.7rem;
          text-transform: uppercase;
          padding: 2px 6px;
          border-radius: 4px;
          background: #4a5568;
        }
        .rarity-tag.uncommon { color: #86efac; }
        .rarity-tag.rare { color: #93c5fd; }
        .rarity-tag.epic { color: #c084fc; }
        .rarity-tag.legendary { color: #fde047; }
      `}</style>
    </div>
  );
};

export default ShopOverlay;
