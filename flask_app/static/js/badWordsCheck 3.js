/**
 * BadWordsCheck - Profanity Detection Library
 * A comprehensive bad word filter that supports both English and Chinese profanity detection
 * Uses dual detection methods: keyword matching and regex pattern matching
 * Can be used standalone or imported as a module into other projects
 * 
 * Features:
 * - Detects over 150 inappropriate words and phrases
 * - Supports multiple languages (English, Chinese, internet slang)
 * - Regex patterns catch variations and creative spellings
 * - Extensible - allows adding custom words and patterns
 * - Browser and Node.js compatible
 * 
 * @author AI Assistant
 * @version 1.0.0
 */

class BadWordsCheck {
    constructor() {
        this.init();
    }

    /**
     * Initialize the word dictionary and regex patterns
     * Sets up comprehensive lists of inappropriate words and flexible regex patterns
     * This method is called automatically when creating a new BadWordsCheck instance
     */
    init() {
        /**
         * Profanity Filter Word List - Inclusion Criteria and Scope
         * 
         * This list contains words and phrases that are filtered to maintain a respectful 
         * and inclusive environment for all users. The inclusion criteria are:
         * 
         * 1. General Profanity: Common vulgar and obscene language (English and Chinese)
         * 2. Sexual Content: Explicit sexual references and anatomical terms
         * 3. Internet Slang: Abbreviated profanity commonly used in online communication
         * 4. Hate Speech: Terms that target individuals or groups based on:
         *    - Ethnicity and race
         *    - Religion and faith
         *    - Nationality and origin
         * 5. Harassment: Phrases expressing violence, death wishes, or personal attacks
         * 
         * Cultural Context and Nuanced Terms:
         * - Some terms have complex cultural meanings that may be offensive in certain contexts
         * - Religious terms (lines 58-59): Derogatory combinations targeting specific faiths
         * - Ethnic/racial slurs (lines 60-61): Terms with harmful historical or cultural connotations
         * - These are included to prevent harassment and maintain community standards
         * - The filter aims to block clearly offensive usage while being context-aware
         * 
         * Maintenance: This list should be reviewed periodically to ensure it remains
         * appropriate and effective. Consider cultural sensitivity and evolving language.
         */
        this.badWords = [
            'fuck', 'fucking', 'fucked', 'fucker', 'fck', 'fuk', 'f*ck', 'f**k',
            'shit', 'shitty', 'bullshit', 'sh*t', 'sh1t',
            'damn', 'damned', 'dammit', 'd*mn',
            'bitch', 'bitchy', 'b*tch', 'b1tch',
            'asshole', 'ass', 'arse', 'a**hole', 'a*s',
            'bastard', 'b*stard',
            'crap', 'crappy', 'cr*p',
            'hell', 'bloody hell',
            'penis', 'vagina', 'cock', 'dick', 'pussy', 'boobs', 'tits',
            'sex', 'sexy', 'porn', 'pornography', 'nude', 'naked',
            'wtf', 'stfu', 'gtfo', 'omfg', 'lmfao',
            '操', '草', '艹', '曹', '屮', '肏',
            '傻逼', '傻B', '傻b', '沙比', '煞笔', '傻比',
            '他妈的', '她妈的', '妈的', '你妈的', '你妈',
            '狗屎', '屎', '拉屎', '吃屎',
            '混蛋', '王八蛋', 'turtle egg', '乌龟蛋',
            '婊子', '贱人', '贱货', '荡妇', '骚货',
            '靠', '靠你妈', '日', '日你', '干你',
            '卧槽', '我操', '我草', '我艹',
            '妈蛋', '蛋疼', '疼你妈',
            '屌', '吊', '屌丝', '吊丝',
            '逼', '牛逼', '装逼', '傻逼',
            '尼玛', '你妹', '你大爷',
            '支那', '小日本', '棒子', '阿三', '黑鬼',
            '死台湾', '湾湾', '弯弯',
            'sb', 'SB', 'cnm', 'CNM', 'nmsl', 'NMSL',
            'wtf', 'WTF', 'stfu', 'STFU',
            'cao', 'ri', 'gan', 'tm', 'md',
            // Religious slurs: Derogatory terms targeting specific religious groups
            // These combine religious identifiers with offensive language
            '绿教', '清真教', '穆斯林狗', '真主垃圾',
            '基督教狗', '佛教傻逼', '道教垃圾',
            // Ethnic and racial slurs: Terms with harmful cultural/historical connotations
            // These target people based on ethnicity, race, or skin color
            '黄皮猴子', '白皮猪', '黑人滚', '犹太狗',
            // Nationality-based slurs: Derogatory terms targeting national/ethnic origins
            // These use offensive stereotypes and demeaning language
            '印度阿三', '越南猴子', '韩国棒子',
            '6324', '草泥马', '法克', 'fxxk',
            '你妈死了', '全家死光', '去死吧',
            '脑残', '智障', '弱智', '白痴', '蠢货',
            '垃圾', '人渣', '败类', '废物', '狗东西',
            '做你妈', '透你', 'qnmlgb', 'qnmd',
            'djb', 'dgl', 'gcd', 'tmd'
        ];

        this.patterns = [
            /f+u+c+k+/gi,
            /s+h+i+t+/gi,
            /b+i+t+c+h+/gi,
            /a+s+s+h+o+l+e+/gi,
            /d+a+m+n+/gi,
            /[操草艹曹屮肏]+/g,
            /[傻沙煞][逼比Ｂb]+/g,
            /[他她你][妈麻马玛]的*/g,
            /[狗够勾][屎史失湿]+/g,
            /[混昏婚][蛋淡但]+/g,
            /[王忘网][八巴爸][蛋淡但]+/g,
            /[婊表标彪][子梓紫籽]+/g,
            /[贱见健剑][人任仁忍]+/g,
            /[屌吊鸟叼调][丝死司思]+/g,
            /\b(sb|SB|cnm|CNM|nmsl|NMSL|cao|ri|gan|tm|md|qnmd|qnmlgb)\b/g,
            /[＊\*]+[操草艹fuck]+[＊\*]*/gi,
            /[操草艹][你ni][妈ma马]/gi,
            /[去死][吧把ba]/gi,
        ];

        console.log('🛡️ BadWordsCheck initialized with', this.badWords.length, 'words and', this.patterns.length, 'patterns');
    }

    /**
     * Check if text contains profanity or inappropriate language
     * Uses both keyword matching and regex pattern detection for comprehensive coverage
     * @param {string} text - The text to check for inappropriate content
     * @returns {boolean} True if profanity is detected, false if text is clean
     */
    isProfane(text) {
        if (!text || typeof text !== 'string') {
            return false;
        }

        const normalizedText = text.toLowerCase().trim();
        
        // Method 1: Direct keyword matching - checks for exact word matches in our dictionary
        for (let word of this.badWords) {
            if (normalizedText.includes(word.toLowerCase())) {
                console.log('🔴 Keyword match found:', word);
                return true;
            }
        }

        // Method 2: Regex pattern matching - catches variations, creative spellings, and character substitutions
        for (let pattern of this.patterns) {
            if (pattern.test(text)) {
                console.log('🔴 Pattern match found:', pattern);
                return true;
            }
        }

        return false;
    }

    /**
     * Analyze text and return detailed information about any profanity found
     * Provides comprehensive analysis including what was detected and how it was detected
     * @param {string} text - The text to analyze for inappropriate content
     * @returns {Object} Analysis results containing isProfane flag, matches array, and count
     */
    analyze(text) {
        if (!text || typeof text !== 'string') {
            return { isProfane: false, matches: [] };
        }

        const matches = [];
        const normalizedText = text.toLowerCase().trim();

        // Check for direct keyword matches in our dictionary
        for (let word of this.badWords) {
            if (normalizedText.includes(word.toLowerCase())) {
                matches.push({ type: 'keyword', word: word });
            }
        }

        // Check for regex pattern matches to catch variations and creative spellings
        for (let pattern of this.patterns) {
            const regexMatches = text.match(pattern);
            if (regexMatches) {
                regexMatches.forEach(match => {
                    matches.push({ type: 'pattern', word: match, pattern: pattern.toString() });
                });
            }
        }

        return {
            isProfane: matches.length > 0,
            matches: matches,
            count: matches.length
        };
    }

    /**
     * Filter and replace profanity with asterisks or custom replacement characters
     * Cleans text by replacing inappropriate words while preserving the original text structure
     * @param {string} text - The text to filter and clean
     * @param {string} replacement - Character to use for replacement (default: '*')
     * @returns {string} The filtered text with profanity replaced
     */
    filter(text, replacement = '*') {
        if (!text || typeof text !== 'string') {
            return text;
        }

        let filteredText = text;

        // Replace direct keyword matches with appropriate number of replacement characters
        for (let word of this.badWords) {
            const regex = new RegExp(word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
            filteredText = filteredText.replace(regex, replacement.repeat(word.length));
        }

        // Replace regex pattern matches with replacement characters maintaining original length
        for (let pattern of this.patterns) {
            filteredText = filteredText.replace(pattern, (match) => replacement.repeat(match.length));
        }

        return filteredText;
    }

    /**
     * Add custom inappropriate words to the detection dictionary
     * Extends the library's vocabulary with project-specific or newly discovered inappropriate terms
     * @param {string|Array} words - Single word (string) or multiple words (array) to add
     */
    addWords(words) {
        if (Array.isArray(words)) {
            this.badWords.push(...words);
        } else if (typeof words === 'string') {
            this.badWords.push(words);
        }
        console.log('🔧 Added', Array.isArray(words) ? words.length : 1, 'custom words');
    }

    /**
     * Add custom regex patterns for advanced profanity detection
     * Allows detection of creative spellings, character substitutions, and complex variations
     * @param {RegExp|Array} patterns - Single regex pattern or array of patterns to add
     */
    addPatterns(patterns) {
        if (Array.isArray(patterns)) {
            this.patterns.push(...patterns);
        } else if (patterns instanceof RegExp) {
            this.patterns.push(patterns);
        }
        console.log('🔧 Added', Array.isArray(patterns) ? patterns.length : 1, 'custom patterns');
    }

    /**
     * Get statistics about the current word dictionary and patterns
     * Useful for monitoring library configuration and debugging detection coverage
     * @returns {Object} Statistics including total words, patterns, and version info
     */
    getStats() {
        return {
            totalWords: this.badWords.length,
            totalPatterns: this.patterns.length,
            version: '1.0.0'
        };
    }
}

// Export the class for external use - makes it available globally in browser environments
if (typeof window !== 'undefined') {
    window.BadWordsCheck = BadWordsCheck;
}

// Node.js module support - allows importing in server-side Node.js applications
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BadWordsCheck;
}